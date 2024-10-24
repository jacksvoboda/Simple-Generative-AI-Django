# pylint: disable=line-too-long

import logging

import requests

def run_model(model_obj, prompt, user='openai_user', extras=None):
    if extras is None:
        extras = {}

    parameters = model_obj.fetch_parameters()

    logging.info('1) paramters fetched from model form: %s', parameters)

    #get system prompt
    system_prompt = parameters.get('system_prompt', '')

    system_prompt_position = parameters.get('system_prompt_position', 'append') # 'append', 'prepend', 'bookend'

    messages = extras.get('messages', [])

    messages.append({
        'role': 'user',
        'content': prompt
    })

    #add system prompt to messages for request object

    if system_prompt_position in ('prepend', 'bookend',):
        messages.insert(0, system_prompt)

    if system_prompt_position in ('append', 'bookend',):
        messages.append({
            'role': 'system',
            'content': system_prompt
        })

    model_type = parameters.get('openai_model', 'gpt-3.5-turbo')

    model_parameters = parameters.get(model_type, {})

    request_obj = {
        'model': model_type,
        'user': user,
        'messages': messages,
    }

    request_obj.update(model_parameters)

    # Some parameters to include:
    # *all coefficients can go above 2 or below 0 where negative values will have inverse effects, and values above 2 will have strong effects but greatly increase the possibility of malfunction.
    #   temperature (randomness where higher is more random 0 - 2; default = 1),
    #   max_tokens (deprecated for o1 series models. They use 'max_completion_tokens'),
    #   top_p (preference for high likelihood token selection)
    #       Higher = more lenience, i.e. considers all possible tokens.
    #       Lower = strictly high likelihood token selection, i.e. focussed, relevant, constrained answers (0.1 = only top 10% tokens are even considered)
    #       0 - 2; default = 1,
    #   n (number of responses; default = 1),
    #   stop (custom generation stop conditions, up to 4 different conditions; default = null),
    #   frequency_penalty (punishes repetition, scaling with token frequency 0 - 1; default = 0),
    #   presence_penalty (punishes repitition, flatly by token use 0 - 1; default = 0)

    response = requests.post('https://api.openai.com/v1/chat/completions',
          headers = {
              'Content-Type': 'application/json',
              'Authorization': 'Bearer %s' % parameters.get('openai_api_key', '')
          },
          json={
              'model': parameters.get('openai_model', 'gpt-3.5-turbo'),
              'messages': messages,
              'max_tokens': parameters.get('max_tokens', 500),
              'temperature': parameters.get('temperature', 1),
              'top_p': parameters.get('top_p', 1),
              'stop': parameters.get('stop', None)
          }, timeout=60)

    response_json = response.json()

    model_obj.log_request(request_obj, response_json, True)

    return response_json.get('choices', [])[0].get('message', {}).get('content', '(No content returned.)')


def validate_model(model_obj):
    parameters = model_obj.fetch_parameters()

    issues = []

    parameters = model_obj.fetch_parameters()

    if parameters.get('openai_api_key', None) is None:
        issues.append('Add valid "openai_api_key" parameter to model')

    if parameters.get('openai_model', None) is None:
        issues.append('Specify "openai_model" type parameter for model (see https://platform.openai.com/docs/models)')

    return issues
