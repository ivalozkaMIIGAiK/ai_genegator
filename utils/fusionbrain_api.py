import json
import time
import requests

class FusionBrainAPI:

    def __init__(self, url, api_key, secret_key):
        self.URL = url
        self.AUTH_HEADERS = {
            'X-Key': f'Key {api_key}',
            'X-Secret': f'Secret {secret_key}',
        }

    def get_pipeline(self):
        response = requests.get(self.URL + 'key/api/v1/pipelines', headers=self.AUTH_HEADERS)
        response.raise_for_status()
        data = response.json()
        return data[0]['id']

    def generate(self, prompt, pipeline, images=1, width=1024, height=1024):
        params = {
            "type": "GENERATE",
            "numImages": images,
            "width": width,
            "height": height,
            "generateParams": {
                "query": f'{prompt}'
            }
        }

        data = {
            'pipeline_id': (None, pipeline),
            'params': (None, json.dumps(params), 'application/json')
        }
        
        response = requests.post(
            self.URL + 'key/api/v1/pipeline/run', 
            headers=self.AUTH_HEADERS, 
            files=data
        )
        response.raise_for_status()
        data = response.json()
        return data['uuid']

    def check_generation(self, request_id, attempts=15, delay=5):
        while attempts > 0:
            try:
                response = requests.get(
                    self.URL + 'key/api/v1/pipeline/status/' + request_id, 
                    headers=self.AUTH_HEADERS
                )
                response.raise_for_status()
                data = response.json()
                
                if data['status'] == 'DONE':
                    return data['result']['files']
                elif data['status'] == 'FAIL':
                    raise RuntimeError(f"Ошибка генерации: {data.get('error', 'Неизвестная ошибка')}")
                
            except requests.exceptions.RequestException as e:
                # Логируем ошибку, но продолжаем попытки
                print(f"Ошибка при проверке статуса: {str(e)}")
            
            attempts -= 1
            time.sleep(delay)
        
        raise TimeoutError("Превышено время ожидания генерации изображения")