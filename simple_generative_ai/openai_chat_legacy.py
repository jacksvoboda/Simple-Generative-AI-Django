# pylint: disable=line-too-long

import importlib
import logging

import requests

from django.conf import settings
from django.utils import timezone

from ..models import GenerativeAIException

def run_model(model_obj, prompt, user='openai_user', extras=None): # pylint: disable=too-many-locals
    if extras is None:
        extras = {}

    parameters = model_obj.fetch_parameters()

    logging.info('1) paramters fetched from model form: %s', parameters)

    #get system prompt
    system_prompt = parameters.get('system_prompt', '')

    system_prompt_position = parameters.get('system_prompt_position', 'append') # 'append', 'prepend', 'bookend'

    for app in settings.INSTALLED_APPS:
        try:
            gen_ai_module = importlib.import_module('.simple_generative_ai', package=app)

            prompt = gen_ai_module.update_extras_and_prompt(model_obj, prompt, extras)
        except ImportError:
            pass
        except AttributeError:
            pass

    messages = extras.get('messages', [])

    if prompt is not None:
        messages.append({
            'role': 'user',
            'content': prompt
        })

    #add system prompt to messages for request object

    if system_prompt_position in ('prepend', 'bookend',):
        messages.insert(0, {
            'role': 'system',
            'content': system_prompt
        })

    if system_prompt_position in ('append', 'bookend',):
        messages.append({
            'role': 'system',
            'content': system_prompt
        })

    model_type = parameters.get('openai_model', 'gpt-3.5-turbo')

    model_parameters = parameters.get("model_parameters", {})

    request_obj = {
        'model': model_type,
        'user': user,
        'messages': messages,
    }

    request_obj.update(model_parameters)

    # Some parameters to include:
    #   temperature (randomness where higher is more random 0 - 2; default = 1),
    #   max_tokens (deprecated for o1 series models. They use 'max_completion_tokens'),
    #   top_p (preference for high likelihood token selection)
    #       Higher = more lenience, i.e. considers all possible tokens.
    #       Lower = strictly high likelihood token selection, i.e. focussed, relevant, constrained answers (0.1 = only top 10% tokens are even considered)
    #       0 - 1; default = 1,
    #   n (number of responses; default = 1),
    #   stop (custom generation stop conditions, up to 4 different conditions; default = null),
    #   frequency_penalty (punishes repetition, scaling with token frequency 0 - 1; default = 0),
    #   presence_penalty (punishes repitition, flatly by token use 0 - 1; default = 0)

    response = requests.post('https://api.openai.com/v1/chat/completions',
          headers = {
              'Content-Type': 'application/json',
              'Authorization': 'Bearer %s' % parameters.get('openai_api_key', '')
          },
          json=request_obj, timeout=60)

    response_json = response.json()

    request_log = model_obj.log_request(request_obj, response_json, True)

    if 'error' in response_json:
        model_obj.enabled = False

        parameters = {}
        parameters['disabled_reason'] = 'Encountered error. See request log ID: %s.' % request_log.pk
        parameters['disabled_time'] = timezone.now().isoformat()

        model_obj.update_parameters(parameters)

        request_log.successful = False
        request_log.save()

        raise GenerativeAIException('Error encountered calling openai_chat_legacy model (%s).' % model_obj)

    return response_json.get('choices', [])[0].get('message', {}).get('content', '(No content returned.)')


def validate_model(model_obj):
    issues = []

    try:
        parameters = model_obj.fetch_parameters()

        if parameters.get('openai_api_key', None) is None:
            issues.append('Add valid "openai_api_key" parameter to model')

        if parameters.get('openai_model', None) is None:
            issues.append('Specify "openai_model" type parameter for model (see https://platform.openai.com/docs/models)')
    except: # pylint: disable=bare-except
        issues.append('Unable to load or validate model "%s". Check that the parameters are formatted correctly.' % model_obj)

    return issues
