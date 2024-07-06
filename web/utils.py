# Copyright 2024 warehauser @ github.com

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     https://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# utils.py

from datetime import datetime

def debug_func(func):
    def func_mod(*args, **kwargs):
        print(f'{func.__name__}({args}, {kwargs}) called at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}.')
        result = func(*args, **kwargs)
        print(f'Result is: {result}')
        return result
    return func_mod

@lambda _: _()
def server_start_time() -> str:
    date = datetime.now()
    return f'{date:%T}'

# print(server_start_time) will print the time the server started running (approx and rounded to the second) and this value is immutable
