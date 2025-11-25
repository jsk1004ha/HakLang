import sys
import re
import random
import time


class HaklangInterpreterGPT:
    """
    기존 interpreter.py 의 모든 기능을 유지하면서 아래와 같은 새로운 문법을 추가합니다.

    새 문법 요약:
    - 이학범<expr>: 표현식의 값을 뒤집습니다. 숫자는 부호를 반전하고, 문자열이나 리스트는 순서를 반대로 하고, bool 은 not 처리합니다.
    - 미추홀구[리스트명]: 리스트를 오름차순으로 정렬합니다.
    - 용현동[리스트명]: 리스트를 내림차순으로 정렬합니다.
    - 데이비드(expr): 표현식을 평가한 결과를 디버그로 출력합니다.
    - 시간먹기(expr): expr 초 만큼 대기합니다.
    - [함수명]미쉥물 연료 젼줴(args): 함수 호출을 지연시켜 프로그램이 끝난 뒤 실행합니다.
    - 쿰쳑쿰쳑<statement>: 지정한 구문을 두 번 실행합니다.
    - 저 쿰쳑 안먹었는데요…: 한 줄 주석입니다. 뒤따르는 모든 내용은 무시됩니다.
    - 아빠와나[변수명]: 변수의 값을 스택에 push 합니다.
    - 아빠와 나[변수명]: 스택에서 pop 하여 변수에 저장합니다.
    - 조건식에서 "… 야 오루페 …": 두 조건을 OR 연산합니다.
    - 조건식에서 "… 야 조깜베 …": 두 조건을 AND 연산합니다.
    - 표현식에서 "… 루피 함 안아보자 …": 문자열이나 리스트를 연결합니다.
    - 표현식에서 "… 남자 중의 남자 …": 두 숫자 중 큰 값을 반환합니다.
    """

    def __init__(self):
        # 기존 인터프리터와 동일한 상태 변수들
        self.variables = {}
        self.variable_types = {}
        self.functions = {}
        self.protected_vars = set()
        self.in_block = False
        self.block_buffer = []
        self.block_type = None
        self.block_context = {}
        self.if_blocks = []
        self.if_condition_met = False
        self.break_flag = False
        self.return_value = None
        self.return_flag = False

        # GPT 확장용 추가 상태
        self.stack = []              # 아빠와 나 스택
        self.deferred_calls = []     # 지연 함수 호출 리스트
        self.double_exec_flag = False  # 다음 라인을 두 번 실행하는 플래그

    def execute_file(self, filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                code = f.read()
            self.run(code)
        except FileNotFoundError:
            print(f"오류: 파일을 찾을 수 없습니다: {filepath}")
        except Exception as e:
            print(f"오류 발생: {e}")

    def run(self, code):
        lines = code.strip().split('\n')
        if not lines:
            return

        # 프로그램 시작 체크
        if not lines[0].strip().startswith('학범'):
            print("오류: 프로그램은 '학범'으로 시작해야 합니다.")
            return

        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line or line == '학범':
                i += 1
                continue

            try:
                # 블록 안에 있는지 확인
                if self.in_block:
                    # 블록 시작 구분자 처리
                    if len(self.block_buffer) == 0 and line == '학':
                        i += 1
                        continue

                    # 블록 종료 조건 확인
                    is_block_end = False
                    if self.block_type == 'while' and line == '귤한봉지':
                        is_block_end = True
                    elif self.block_type in ['for', 'function', 'if', 'elseif', 'else'] and line == '학':
                        is_block_end = True
                    elif line in ['}귤한봉지', '}그챼']:
                        is_block_end = True

                    if is_block_end:
                        result = self.execute_block()
                        self.in_block = False
                        self.block_buffer = []
                        self.block_type = None
                        self.block_context = {}
                    else:
                        self.block_buffer.append(line)
                    i += 1
                    continue

                # 쿰쳑쿰쳑 구문: 다음 구문을 두 번 실행
                if line.startswith('쿰쳑쿰쳑'):
                    inner = line[len('쿰쳑쿰쳑'):].strip()
                    if inner:
                        # 한 줄 안에 구문을 바로 실행
                        for _ in range(2):
                            if not self.process_line(inner):
                                print(f"오류: 알 수 없는 구문입니다: {inner}")
                                sys.exit(1)
                    else:
                        # 별도의 라인을 두 번 실행할 플래그 설정
                        self.double_exec_flag = True
                    i += 1
                    continue

                # 주석: 저 쿰쳑 안먹었는데요 로 시작하는 줄 무시
                if line.startswith('저 쿰쳑 안먹었는데요'):
                    i += 1
                    continue

                # double_exec_flag 가 설정되어 있으면 해당 라인을 두 번 실행
                if self.double_exec_flag:
                    # 두 번 실행 후 플래그 해제
                    for _ in range(2):
                        if not self.process_line(line):
                            print(f"오류: 알 수 없는 구문입니다: {line}")
                            sys.exit(1)
                    self.double_exec_flag = False
                    i += 1
                    continue

                # 일반적인 라인 처리
                if not self.process_line(line):
                    print(f"오류 (Line {i+1}): 알 수 없는 구문입니다: {line}")
                    sys.exit(1)
            except Exception as e:
                print(f"오류 (Line {i+1}): {e}")
                sys.exit(1)

            i += 1

        # 프로그램 종료 후 지연 함수 호출 실행
        for func_name, args in self.deferred_calls:
            try:
                self.call_function(func_name, args)
            except Exception as e:
                print(f"오류: 지연 함수 '{func_name}' 호출 중 오류: {e}")

    def process_line(self, line):
        """
        한 줄의 코드를 해석하고 실행합니다.
        기존 interpreter.py 에 정의된 모든 기능을 포함하면서 새로운 GPT 확장 문법을 추가합니다.
        """

        # 0. break
        if line == '몸무게0.1톤':
            self.break_flag = True
            return True

        # 0b. return
        if line.startswith('꺼억'):
            self.return_flag = True
            if len(line) > 2:
                return_expr = line[2:].strip()
                if return_expr:
                    self.return_value = self.evaluate_expression(return_expr)
            return True

        # 0c. Boolean literals (preserve 기존 동작)
        if line == '야오루폐' or line == '야조깜베':
            return True

        # 1. 변수 선언 (기존 구현 그대로)
        match_int = re.match(r'\{BMI30\}\[(?:\((.+?)\)|(.+?))\](포자맨)?', line)
        if match_int:
            var_name = match_int.group(1) or match_int.group(2)
            protected = match_int.group(3) is not None
            self.variables[var_name] = 30
            self.variable_types[var_name] = 'int'
            if protected:
                self.protected_vars.add(var_name)
            return True

        match_float7 = re.match(r'\{BMI30\.7\}\[(?:\((.+?)\)|(.+?))\](포자맨)?', line)
        if match_float7:
            var_name = match_float7.group(1) or match_float7.group(2)
            protected = match_float7.group(3) is not None
            self.variables[var_name] = 30.7
            self.variable_types[var_name] = 'float7'
            if protected:
                self.protected_vars.add(var_name)
            return True

        match_float15 = re.match(r'\{BMI30\.7ㅋㅋ\}\[(?:\((.+?)\)|(.+?))\](포자맨)?', line)
        if match_float15:
            var_name = match_float15.group(1) or match_float15.group(2)
            protected = match_float15.group(3) is not None
            self.variables[var_name] = 30.7
            self.variable_types[var_name] = 'float15'
            if protected:
                self.protected_vars.add(var_name)
            return True

        match_str = re.match(r'\{BMI\}\[(?:\((.+?)\)|(.+?))\](포자맨)?', line)
        if match_str:
            var_name = match_str.group(1) or match_str.group(2)
            protected = match_str.group(3) is not None
            self.variables[var_name] = ""
            self.variable_types[var_name] = 'str'
            if protected:
                self.protected_vars.add(var_name)
            return True

        match_list = re.match(r'\{BMI\[(.+?)\]\}\[(?:\((.+?)\)|(.+?))\](포자맨)?', line)
        if match_list:
            list_type = match_list.group(1)
            var_name = match_list.group(2) or match_list.group(3)
            protected = match_list.group(4) is not None
            if list_type == '30':
                self.variable_types[var_name] = 'list_int'
            elif list_type == '30.7':
                self.variable_types[var_name] = 'list_float7'
            elif list_type == '30.7ㅋㅋ':
                self.variable_types[var_name] = 'list_float15'
            else:
                self.variable_types[var_name] = 'list_str'
            self.variables[var_name] = []
            if protected:
                self.protected_vars.add(var_name)
            return True

        # 2. 문자열 할당
        match_str_assign = re.match(r'\[(?:\((.+?)\)|(.+?))\]꿀꺽<\'(.+)\'', line)
        if match_str_assign:
            var_name = match_str_assign.group(1) or match_str_assign.group(2)
            value_str = match_str_assign.group(3)
            if var_name not in self.variables:
                print(f"오류: 정의되지 않은 변수 '{var_name}'")
                sys.exit(1)
            if self.variable_types[var_name] == 'str':
                self.variables[var_name] = value_str
            else:
                print(f"오류: '{var_name}'은(는) 문자열 변수가 아닙니다.")
                sys.exit(1)
            return True

        # 2b. 변수 증감 연산
        match_increment = re.match(r'\[(?:\((.+?)\)|(.+?))\]꿀꺽<(.+)', line)
        if match_increment:
            var_name = match_increment.group(1) or match_increment.group(2)
            operation = match_increment.group(3).strip()
            if var_name not in self.variables:
                print(f"오류: 정의되지 않은 변수 '{var_name}'")
                sys.exit(1)
            delta = 0
            if operation == '밥':
                delta = 1
            elif operation == '빵':
                delta = 0.1
            elif operation.startswith('고기'):
                count = operation.count('고기')
                delta = 0.01 * (0.1 ** (count - 1))
            elif operation == '야채':
                delta = -1
            elif operation == '설사약':
                delta = -0.1
            elif operation.startswith('포자빵'):
                count = operation.count('포자빵')
                delta = -0.01 * (0.1 ** (count - 1))
            else:
                print(f"오류: 알 수 없는 연산 '{operation}'")
                sys.exit(1)
            var_type = self.variable_types[var_name]
            if var_type in ('int', 'float7', 'float15'):
                self.variables[var_name] += delta
                if var_type == 'int':
                    self.variables[var_name] = int(self.variables[var_name])
            else:
                print(f"오류: '{var_name}' 변수에 대한 꿀꺽 연산은 지원되지 않습니다.")
                sys.exit(1)
            return True

        # 2c. 리스트 할당
        match_list_assign = re.match(r'\[(?:\((.+?)\)|(.+?))\]쿰척<"\[(.*)\]"', line)
        if match_list_assign:
            var_name = match_list_assign.group(1) or match_list_assign.group(2)
            values_str = match_list_assign.group(3)
            if var_name not in self.variable_types or (not self.variable_types[var_name].startswith('list')):
                print(f"오류: 정의되지 않은 리스트 변수 '{var_name}'")
                sys.exit(1)
            parts = [p.strip() for p in values_str.split(',')] if values_str.strip() != '' else []
            t = self.variable_types[var_name]
            parsed = []
            for p in parts:
                try:
                    if t == 'list_int':
                        parsed.append(int(p))
                    elif t in ('list_float7', 'list_float15'):
                        parsed.append(float(p))
                    else:
                        parsed.append(p)
                except ValueError:
                    print(f"오류: '{p}'은(는) 리스트 '{var_name}'의 형식에 맞지 않습니다.")
                    sys.exit(1)
            self.variables[var_name] = parsed
            return True

        # 2d. 리스트 정렬 (신규 문법)
        match_sort_asc = re.match(r'미추홀구\[(.+?)\]', line)
        if match_sort_asc:
            list_name = match_sort_asc.group(1).strip()
            if list_name not in self.variables or not self.variable_types[list_name].startswith('list'):
                print(f"오류: 정의되지 않은 리스트 변수 '{list_name}'")
                sys.exit(1)
            try:
                self.variables[list_name] = sorted(self.variables[list_name])
            except Exception as e:
                print(f"오류: 리스트 정렬 실패: {e}")
                sys.exit(1)
            return True
        match_sort_desc = re.match(r'용현동\[(.+?)\]', line)
        if match_sort_desc:
            list_name = match_sort_desc.group(1).strip()
            if list_name not in self.variables or not self.variable_types[list_name].startswith('list'):
                print(f"오류: 정의되지 않은 리스트 변수 '{list_name}'")
                sys.exit(1)
            try:
                self.variables[list_name] = sorted(self.variables[list_name], reverse=True)
            except Exception as e:
                print(f"오류: 리스트 정렬 실패: {e}")
                sys.exit(1)
            return True

        # 3. 출력
        if line.endswith('쿰척<쿰척'):
            content = line[:-5]
            self.handle_print(content, newline=True)
            return True
        elif line.endswith('<쿰척'):
            content = line[:-3]
            self.handle_print(content, newline=False)
            return True

        # 4. 단독 입력 (기존)
        if line == '쿰척<()':
            input()
            return True
        if line == '쿰척<쿰척()':
            input()
            print()
            return True

        # 5. 변수 입력 (기존)
        match_input_var = re.match(r'쿰척<\((.+?)\)', line)
        if match_input_var:
            var_name = match_input_var.group(1)
            if var_name in self.variables:
                val_str = input()
                try:
                    if self.variable_types[var_name] == 'int':
                        self.variables[var_name] = int(val_str)
                    elif self.variable_types[var_name] in ('float7', 'float15'):
                        self.variables[var_name] = float(val_str)
                    elif self.variable_types[var_name] == 'str':
                        self.variables[var_name] = val_str
                    else:
                        print(f"오류: '{var_name}' 변수 타입은 입력을 지원하지 않습니다.")
                        sys.exit(1)
                except ValueError:
                    print(f"오류: '{val_str}'은(는) 변수 '{var_name}'에 적합한 값이 아닙니다.")
                    sys.exit(1)
            else:
                print(f"오류: 정의되지 않은 변수 '{var_name}'")
                sys.exit(1)
            return True

        # 6. for 문 (기존)
        match_for = re.match(r'그챼\((.+?)그챼(.+?)그챼(.+?)\)그챼', line)
        if match_for:
            init_stmt = match_for.group(1).strip()
            cond_expr = match_for.group(2).strip()
            step_stmt = match_for.group(3).strip()
            self.in_block = True
            self.block_type = 'for'
            self.block_context = {'init': init_stmt, 'cond': cond_expr, 'step': step_stmt}
            return True

        # 7. if, elseif, else (기존)
        match_if = re.match(r'비만인가\[(.+?)\]알아보자', line)
        if match_if:
            cond_expr = match_if.group(1).strip()
            self.in_block = True
            self.block_type = 'if'
            self.block_context = {'cond': cond_expr}
            self.if_condition_met = False
            return True

        match_elseif = re.match(r'학범이는비만일수도있음\[(.+?)\]', line)
        if match_elseif:
            cond_expr = match_elseif.group(1).strip()
            self.in_block = True
            self.block_type = 'elseif'
            self.block_context = {'cond': cond_expr}
            return True

        if line == '학범이는비만이아님':
            self.in_block = True
            self.block_type = 'else'
            self.block_context = {}
            return True

        if line == '학범이는비만임':
            return True

        # 8. while (기존)
        match_while = re.match(r'나살뺄거야\((.+?)\)', line)
        if match_while:
            cond_expr = match_while.group(1).strip()
            self.in_block = True
            self.block_type = 'while'
            self.block_context = {'cond': cond_expr}
            return True

        if line == '5분':
            return True

        # 9. 함수 정의 (기존)
        match_func_def = re.match(r'\[(.+?)\]미쉥물 ?연료\[(.*)\]전줴', line)
        if match_func_def:
            func_name = match_func_def.group(1).strip()
            params_str = match_func_def.group(2).strip()
            params = [p.strip() for p in params_str.split(',')] if params_str else []
            self.in_block = True
            self.block_type = 'function'
            self.block_context = {'name': func_name, 'params': params}
            return True

        # 9b. 지연 함수 호출 (신규)
        match_deferred = re.match(r'\[(.+?)\]미쉥물 ?연료 ?젼줴\((.*)\)', line)
        if match_deferred:
            func_name = match_deferred.group(1).strip()
            args_str = match_deferred.group(2).strip()
            args = []
            if args_str:
                arg_parts = [a.strip() for a in args_str.split(',')]
                for arg in arg_parts:
                    args.append(self.evaluate_expression(arg))
            # 지연 호출 목록에 추가
            self.deferred_calls.append((func_name, args))
            return True

        # 10. 변수/리스트 초기화 (기존)
        match_reset = re.match(r'간장먹고\[(.+?)\]치기', line)
        if match_reset:
            var_name = match_reset.group(1).strip()
            if var_name not in self.variables:
                print(f"오류: 정의되지 않은 변수 '{var_name}'")
                sys.exit(1)
            var_type = self.variable_types[var_name]
            if var_type == 'int':
                self.variables[var_name] = 30
            elif var_type == 'float7' or var_type == 'float15':
                self.variables[var_name] = 30.7
            elif var_type.startswith('list'):
                self.variables[var_name] = []
            elif var_type == 'str':
                self.variables[var_name] = ""
            return True

        # 10b. 랜덤 값 할당 (기존)
        match_random_var = re.match(r'포자\[(.+?)\]', line)
        if match_random_var:
            var_name = match_random_var.group(1).strip()
            if var_name not in self.variables:
                print(f"오류: 정의되지 않은 변수 '{var_name}'")
                sys.exit(1)
            if var_name in self.protected_vars:
                return True
            self.assign_random_value(var_name)
            return True
        if line == '포자빵':
            for var_name in self.variables.keys():
                if var_name not in self.protected_vars:
                    self.assign_random_value(var_name)
            return True

        # 11. 함수 호출 (기존)
        match_func_call = re.match(r'\[(.+?)\]\((.*)\)', line)
        if match_func_call:
            func_name = match_func_call.group(1).strip()
            args_str = match_func_call.group(2).strip()
            if func_name in self.functions:
                args = []
                if args_str:
                    arg_parts = args_str.split(',')
                    for arg in arg_parts:
                        args.append(self.evaluate_expression(arg.strip()))
                self.call_function(func_name, args)
                return True

        # 12. 리스트 요소 출력 (기존)
        match_list_print = re.match(r'\[(?:\((.+?)\)|(.+?))\]쿰척\[(\d+)\]', line)
        if match_list_print:
            var_name = match_list_print.group(1) or match_list_print.group(2)
            idx = int(match_list_print.group(3)) - 1
            if var_name not in self.variables:
                print(f"오류: 정의되지 않은 리스트 변수 '{var_name}'")
                sys.exit(1)
            if not self.variable_types[var_name].startswith('list'):
                print(f"오류: '{var_name}'은(는) 리스트가 아닙니다.")
                sys.exit(1)
            lst = self.variables[var_name]
            if idx < 0 or idx >= len(lst):
                print(f"오류: 인덱스 {idx+1} 는 리스트 범위를 벗어납니다.")
                sys.exit(1)
            elem = lst[idx]
            t = self.variable_types[var_name]
            if t == 'list_int':
                print(elem)
            elif t == 'list_float7':
                print(f"{elem:.7f}")
            elif t == 'list_float15':
                print(f"{elem:.15f}")
            else:
                print(elem)
            return True

        # 13. 스택 연산 (신규)
        match_push = re.match(r'아빠와나\[(.+?)\]', line)
        if match_push:
            var_name = match_push.group(1).strip()
            if var_name not in self.variables:
                print(f"오류: 정의되지 않은 변수 '{var_name}'")
                sys.exit(1)
            self.stack.append(self.variables[var_name])
            return True
        match_pop = re.match(r'아빠와 나\[(.+?)\]', line)
        if match_pop:
            var_name = match_pop.group(1).strip()
            if not self.stack:
                print("오류: 스택이 비어있어 pop 할 수 없습니다.")
                sys.exit(1)
            value = self.stack.pop()
            # 타입 추론하여 변수에 설정
            if isinstance(value, int):
                self.variables[var_name] = value
                self.variable_types[var_name] = 'int'
            elif isinstance(value, float):
                self.variables[var_name] = value
                self.variable_types[var_name] = 'float7'
            elif isinstance(value, str):
                self.variables[var_name] = value
                self.variable_types[var_name] = 'str'
            elif isinstance(value, list):
                self.variables[var_name] = value
                # 리스트 타입 추론은 간단히 list_int 로 지정
                self.variable_types[var_name] = 'list_int'
            return True

        # 14. 디버그 출력 (신규)
        match_debug = re.match(r'데이비드\((.+)\)', line)
        if match_debug:
            expr = match_debug.group(1).strip()
            val = self.evaluate_expression(expr)
            # 디버그 출력은 표준 출력에 타입과 함께 출력한다
            print(f"[디버그] {expr} = {val}")
            return True

        # 15. 시간먹기 (신규)
        match_sleep = re.match(r'시간먹기\((.+)\)', line)
        if match_sleep:
            expr = match_sleep.group(1).strip()
            duration = self.evaluate_expression(expr)
            try:
                t = float(duration)
                if t < 0:
                    print("오류: 시간은 음수일 수 없습니다.")
                    sys.exit(1)
                time.sleep(t)
            except ValueError:
                print(f"오류: 시간 '{duration}'을(를) 숫자로 변환할 수 없습니다.")
                sys.exit(1)
            return True

        return False

    def assign_random_value(self, var_name):
        var_type = self.variable_types[var_name]
        if var_type == 'int':
            self.variables[var_name] = random.randint(-1000, 1000)
        elif var_type == 'float7' or var_type == 'float15':
            self.variables[var_name] = random.uniform(-1000.0, 1000.0)
        elif var_type == 'str':
            words = ['학범', '비만', '하악', '귤', '쿰척', '쑤학']
            self.variables[var_name] = random.choice(words)
        elif var_type.startswith('list_'):
            size = random.randint(3, 5)
            if var_type == 'list_int':
                self.variables[var_name] = [random.randint(-100, 100) for _ in range(size)]
            elif var_type in ('list_float7', 'list_float15'):
                self.variables[var_name] = [random.uniform(-100.0, 100.0) for _ in range(size)]
            elif var_type == 'list_str':
                words = ['학범', '비만', '하악', '귤', '쿰척']
                self.variables[var_name] = [random.choice(words) for _ in range(size)]

    def call_function(self, func_name, args):
        if func_name not in self.functions:
            print(f"오류: 정의되지 않은 함수 '{func_name}'")
            sys.exit(1)
        params, body = self.functions[func_name]
        if len(args) != len(params):
            print(f"오류: 함수 '{func_name}'는 {len(params)}개의 매개변수가 필요하지만 {len(args)}개가 전달되었습니다.")
            sys.exit(1)
        # 현재 변수 상태 저장
        saved_vars = self.variables.copy()
        saved_types = self.variable_types.copy()
        # 매개변수 설정
        for param, arg in zip(params, args):
            if isinstance(arg, int):
                self.variables[param] = arg
                self.variable_types[param] = 'int'
            elif isinstance(arg, float):
                self.variables[param] = arg
                self.variable_types[param] = 'float7'
            elif isinstance(arg, str):
                self.variables[param] = arg
                self.variable_types[param] = 'str'
            elif isinstance(arg, list):
                self.variables[param] = arg
                self.variable_types[param] = 'list_int'
        # 함수 본문 실행
        self.return_flag = False
        self.return_value = None
        for body_line in body:
            if not self.process_line(body_line):
                print(f"오류: 함수 본문 오류: {body_line}")
                sys.exit(1)
            if self.return_flag:
                break
        result = self.return_value
        # 변수 상태 복원
        self.variables = saved_vars
        self.variable_types = saved_types
        self.return_flag = False
        self.return_value = None
        return result

    def execute_block(self):
        # 기존 interpreter.py 의 execute_block 을 거의 그대로 사용
        if self.block_type == 'function':
            func_name = self.block_context['name']
            params = self.block_context['params']
            self.functions[func_name] = (params, self.block_buffer[:])
            return
        elif self.block_type == 'if':
            cond_expr = self.block_context['cond']
            if self.evaluate_condition(cond_expr):
                self.if_condition_met = True
                self.execute_nested_block(self.block_buffer)
            return
        elif self.block_type == 'elseif':
            cond_expr = self.block_context['cond']
            if not self.if_condition_met and self.evaluate_condition(cond_expr):
                self.if_condition_met = True
                self.execute_nested_block(self.block_buffer)
            return
        elif self.block_type == 'else':
            if not self.if_condition_met:
                self.execute_nested_block(self.block_buffer)
            self.if_condition_met = False
            return
        elif self.block_type == 'for':
            init_stmt = self.block_context['init']
            cond_expr = self.block_context['cond']
            step_stmt = self.block_context['step']
            if not self.process_line(init_stmt):
                print(f"오류: for문 초기화 구문 오류: {init_stmt}")
                sys.exit(1)
            max_iterations = 100000
            iterations = 0
            while iterations < max_iterations:
                if not self.evaluate_condition(cond_expr):
                    break
                self.break_flag = False
                self.execute_nested_block(self.block_buffer)
                if self.break_flag:
                    self.break_flag = False
                    break
                if not self.process_line(step_stmt):
                    print(f"오류: for문 진행 구문 오류: {step_stmt}")
                    sys.exit(1)
                iterations += 1
            if iterations >= max_iterations:
                print("오류: for문이 너무 많이 반복되었습니다 (무한 루프?)")
                sys.exit(1)
        elif self.block_type == 'while':
            cond_expr = self.block_context['cond']
            max_iterations = 100000
            iterations = 0
            while iterations < max_iterations:
                if not self.evaluate_condition(cond_expr):
                    break
                self.break_flag = False
                self.execute_nested_block(self.block_buffer)
                if self.break_flag:
                    self.break_flag = False
                    break
                iterations += 1
            if iterations >= max_iterations:
                print("오류: while문이 너무 많이 반복되었습니다 (무한 루프?)")
                sys.exit(1)

    def execute_nested_block(self, lines):
        i = 0
        while i < len(lines):
            line = lines[i]
            # 중첩 if/elseif/else 블록 처리
            if re.match(r'비만인가\[.+?\]알아보자', line):
                nested_lines = []
                i += 1
                if i < len(lines) and lines[i] == '학범이는비만임':
                    i += 1
                depth = 1
                while i < len(lines) and depth > 0:
                    if lines[i] == '학':
                        depth -= 1
                        if depth == 0:
                            break
                    elif re.match(r'비만인가\[.+?\]알아보자', lines[i]):
                        depth += 1
                    if depth > 0:
                        nested_lines.append(lines[i])
                    i += 1
                match = re.match(r'비만인가\[(.+?)\]알아보자', line)
                cond_expr = match.group(1).strip()
                if self.evaluate_condition(cond_expr):
                    self.if_condition_met = True
                    self.execute_nested_block(nested_lines)
                else:
                    self.if_condition_met = False
            elif re.match(r'학범이는비만일수도있음\[.+?\]', line):
                nested_lines = []
                i += 1
                if i < len(lines) and lines[i] == '학':
                    i += 1
                depth = 1
                while i < len(lines) and depth > 0:
                    if lines[i] == '학':
                        depth -= 1
                        if depth == 0:
                            break
                    elif re.match(r'비만인가\[.+?\]알아보자', lines[i]):
                        depth += 1
                    if depth > 0:
                        nested_lines.append(lines[i])
                    i += 1
                match = re.match(r'학범이는비만일수도있음\[(.+?)\]', line)
                cond_expr = match.group(1).strip()
                if not self.if_condition_met and self.evaluate_condition(cond_expr):
                    self.if_condition_met = True
                    self.execute_nested_block(nested_lines)
            elif line == '학범이는비만이아님':
                nested_lines = []
                i += 1
                if i < len(lines) and lines[i] == '학':
                    i += 1
                depth = 1
                while i < len(lines) and depth > 0:
                    if lines[i] == '학':
                        depth -= 1
                        if depth == 0:
                            break
                    elif re.match(r'비만인가\[.+?\]알아보자', lines[i]):
                        depth += 1
                    if depth > 0:
                        nested_lines.append(lines[i])
                    i += 1
                if not self.if_condition_met:
                    self.execute_nested_block(nested_lines)
                self.if_condition_met = False
            else:
                if not self.process_line(line):
                    print(f"오류: 본문 오류: {line}")
                    sys.exit(1)
                if self.break_flag or self.return_flag:
                    break
            i += 1

    def evaluate_condition(self, expr):
        expr = expr.strip()
        # 참/거짓 리터럴
        if expr == '야오루폐':
            return True
        if expr == '야조깜베':
            return False
        # 논리 OR 신문법: "... 야 오루페 ..."
        if '야 오루페' in expr:
            parts = expr.split('야 오루페', 1)
            left = self.evaluate_condition(parts[0].strip())
            right = self.evaluate_condition(parts[1].strip())
            return left or right
        # 논리 AND 신문법: "... 야 조깜베 ..."
        if '야 조깜베' in expr:
            parts = expr.split('야 조깜베', 1)
            left = self.evaluate_condition(parts[0].strip())
            right = self.evaluate_condition(parts[1].strip())
            return left and right
        # 비교 연산자 (기존)
        korean_ops = [
            ('비만정상', '<='),
            ('홀쭉정상', '>='),
            ('정상정상', '=='),
            ('정상', '=='),
            ('비만', '<'),
            ('홀쭉', '>'),
        ]
        for korean_op, symbol_op in korean_ops:
            if korean_op in expr:
                parts = expr.split(korean_op, 1)
                if len(parts) == 2:
                    left = self.evaluate_expression(parts[0].strip())
                    right = self.evaluate_expression(parts[1].strip())
                    if symbol_op == '<':
                        return left < right
                    elif symbol_op == '>':
                        return left > right
                    elif symbol_op == '<=':
                        return left <= right
                    elif symbol_op == '>=':
                        return left >= right
                    elif symbol_op == '==':
                        return left == right
        # 나머지는 표현식 평가 후 진리값
        val = self.evaluate_expression(expr)
        return bool(val)

    def evaluate_expression(self, expr):
        expr = expr.strip()
        # unary operator: 이학범<expr>
        if expr.startswith('이학범'):
            inner = expr[len('이학범'):].strip()
            val = self.evaluate_expression(inner)
            if isinstance(val, (int, float)):
                return -val
            elif isinstance(val, str):
                return val[::-1]
            elif isinstance(val, list):
                return list(reversed(val))
            elif isinstance(val, bool):
                return not val
            else:
                return val
        # binary operators with longest match first
        operators = [
            ('루피 함 안아보자', 'concat'),   # concat
            ('남자 중의 남자', 'max'),        # max
            ('비이만하악범', '^'),
            ('학범비만', '*'),
            ('비만학범', '/'),
            ('하악범', '+'),
            ('하악버엄', '-'),
        ]
        for korean_op, op_id in operators:
            if korean_op in expr:
                parts = expr.split(korean_op, 1)
                if len(parts) == 2:
                    left = self.evaluate_expression(parts[0].strip())
                    right = self.evaluate_expression(parts[1].strip())
                    if op_id == 'concat':
                        # 문자열 또는 리스트 연결
                        if isinstance(left, list) and isinstance(right, list):
                            return left + right
                        return str(left) + str(right)
                    elif op_id == 'max':
                        try:
                            return left if left >= right else right
                        except Exception:
                            return left
                    elif op_id == '+':
                        return left + right
                    elif op_id == '-':
                        return left - right
                    elif op_id == '*':
                        return left * right
                    elif op_id == '/':
                        return left / right if right != 0 else 0
                    elif op_id == '^':
                        return left ** right
        # 변수 참조: 'varname'
        if expr.startswith("'") and expr.endswith("'"):
            var_name = expr[1:-1]
            if var_name in self.variables:
                return self.variables[var_name]
            else:
                return 0
        # 숫자
        try:
            if '.' in expr:
                return float(expr)
            else:
                return int(expr)
        except ValueError:
            pass
        # 문자열 리터럴
        if expr.startswith('"') and expr.endswith('"'):
            return expr[1:-1]
        print(f"오류: 표현식을 평가할 수 없습니다: {expr}")
        sys.exit(1)

    def handle_print(self, content_block, newline):
        # 기존 handle_print 함수와 동일
        if content_block.startswith('(') and content_block.endswith(')'):
            inner = content_block[1:-1]
        else:
            inner = content_block
        tokens = re.findall(r'("[^"]*"|\'[^\']*\'|\[[^\]]+\]\[\d+\])', inner)
        output_str = ""
        for token in tokens:
            if token.startswith('"') and token.endswith('"'):
                output_str += token[1:-1]
            elif token.startswith("'") and token.endswith("'"):
                var_name = token[1:-1]
                if var_name in self.variables:
                    val = self.variables[var_name]
                    v_type = self.variable_types[var_name]
                    if v_type == 'int':
                        output_str += str(val)
                    elif v_type == 'float7':
                        output_str += f"{val:.7f}"
                    elif v_type == 'float15':
                        output_str += f"{val:.15f}"
                    elif v_type == 'str':
                        output_str += str(val)
                else:
                    output_str += 'undefined'
            elif token.startswith('[') and re.match(r'\[[^\]]+\]\[\d+\]', token):
                m = re.match(r'\[([^\]]+)\]\[(\d+)\]', token)
                if m:
                    list_name = m.group(1)
                    idx = int(m.group(2)) - 1
                    if list_name in self.variables:
                        lst = self.variables[list_name]
                        if 0 <= idx < len(lst):
                            t = self.variable_types[list_name]
                            elem = lst[idx]
                            if t == 'list_int':
                                output_str += str(elem)
                            elif t == 'list_float7':
                                output_str += f"{elem:.7f}"
                            elif t == 'list_float15':
                                output_str += f"{elem:.15f}"
                            else:
                                output_str += str(elem)
                        else:
                            output_str += 'undefined'
                    else:
                        output_str += 'undefined'
        if newline:
            print(output_str)
        else:
            print(output_str, end='')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("사용법: python interpreter_gpt.py <파일.lhb>")
    else:
        interpreter = HaklangInterpreterGPT()
        interpreter.execute_file(sys.argv[1])