import sys
import re
import random

class HaklangInterpreter:
    def __init__(self):
        self.variables = {}
        self.variable_types = {}  # 'int', 'float7', 'float15'
        self.functions = {}  # function_name -> (params, body_lines)
        self.protected_vars = set()  # variables protected with 포자맨
        self.in_block = False
        self.block_buffer = []
        self.block_type = None  # 'for', 'while', 'function', 'if', 'elseif', 'else'
        self.block_context = {}  # stores context for current block
        self.if_blocks = []  # Stack of if statement blocks
        self.if_condition_met = False  # Track if any condition in if-elseif chain was met
        self.break_flag = False
        self.return_value = None
        self.return_flag = False

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

        # Check if the program starts with '학범'
        if not lines[0].strip().startswith('학범'):
            print("오류: 프로그램은 '학범'으로 시작해야 합니다.")
            return

        for i, line in enumerate(lines):
            line = line.strip()
            if not line or line == '학범':
                continue
            try:
                # Check if we're in a block
                if self.in_block:
                    # Check if this is the opening delimiter (first 학 after block start)
                    if len(self.block_buffer) == 0 and line == '학':
                        # This is the opening delimiter for function/loop body, skip it
                        continue
                    
                    if line in ['귤한봉지', '학', '}귤한봉지', '}그챼']:
                        # End of block
                        result = self.execute_block()
                        self.in_block = False
                        self.block_buffer = []
                        self.block_type = None
                        self.block_context = {}
                    else:
                        # Add to block buffer
                        self.block_buffer.append(line)
                    continue
                
                if not self.process_line(line):
                    print(f"오류 (Line {i+1}): 알 수 없는 구문입니다: {line}")
                    # Unknown syntax -> exit
                    sys.exit(1)
            except Exception as e:
                print(f"오류 (Line {i+1}): {e}")
                sys.exit(1)

    def process_line(self, line):
        # 0. Break and return statements
        if line == '몸무게0.1톤':
            self.break_flag = True
            return True
        
        if line.startswith('꺼억'):
            # return statement: 꺼억 or 꺼억<expr>
            self.return_flag = True
            if len(line) > 2:
                # Extract return value
                return_expr = line[2:].strip()
                if return_expr:
                    self.return_value = self.evaluate_expression(return_expr)
            return True
        
        # 0b. Boolean literals and constants
        if line == '야오루폐':
            # This is True - but standalone, might need context
            return True
        if line == '야조깜베':
            # This is False
            return True
        
        # 1. Variable Declaration
        # 정수: {BMI30}[변수명] or {BMI30}[변수명]포자맨
        # 지원: 기존 형식 {BMI30}[(이름)] 도 허용 (하위 호환)
        match_int = re.match(r'\{BMI30\}\[(?:\((.+?)\)|(.+?))\](포자맨)?', line)
        if match_int:
            var_name = match_int.group(1) or match_int.group(2)
            protected = match_int.group(3) is not None
            self.variables[var_name] = 30
            self.variable_types[var_name] = 'int'
            if protected:
                self.protected_vars.add(var_name)
            return True

        # 유리수(소수점 이하 7자리): {BMI30.7}[변수명] or {BMI30.7}[변수명]포자맨
        match_float7 = re.match(r'\{BMI30\.7\}\[(?:\((.+?)\)|(.+?))\](포자맨)?', line)
        if match_float7:
            var_name = match_float7.group(1) or match_float7.group(2)
            protected = match_float7.group(3) is not None
            self.variables[var_name] = 30.7
            self.variable_types[var_name] = 'float7'
            if protected:
                self.protected_vars.add(var_name)
            return True

        # 유리수(소수점 이하 15자리): {BMI30.7ㅋㅋ}[변수명] or {BMI30.7ㅋㅋ}[변수명]포자맨
        match_float15 = re.match(r'\{BMI30\.7ㅋㅋ\}\[(?:\((.+?)\)|(.+?))\](포자맨)?', line)
        if match_float15:
            var_name = match_float15.group(1) or match_float15.group(2)
            protected = match_float15.group(3) is not None
            self.variables[var_name] = 30.7
            self.variable_types[var_name] = 'float15'
            if protected:
                self.protected_vars.add(var_name)
            return True
        # 문자열 변수: {BMI}[변수명] or {BMI}[변수명]포자맨
        match_str = re.match(r'\{BMI\}\[(?:\((.+?)\)|(.+?))\](포자맨)?', line)
        if match_str:
            var_name = match_str.group(1) or match_str.group(2)
            protected = match_str.group(3) is not None
            self.variables[var_name] = ""
            self.variable_types[var_name] = 'str'
            if protected:
                self.protected_vars.add(var_name)
            return True

        # 리스트 변수: {BMI[타입]}[리스트명] or {BMI[타입]}[리스트명]포자맨
        match_list = re.match(r'\{BMI\[(.+?)\]\}\[(?:\((.+?)\)|(.+?))\](포자맨)?', line)
        if match_list:
            list_type = match_list.group(1)
            var_name = match_list.group(2) or match_list.group(3)
            protected = match_list.group(4) is not None
            # Determine element type from list_type
            if list_type == '30':
                self.variable_types[var_name] = 'list_int'
            elif list_type == '30.7':
                self.variable_types[var_name] = 'list_float7'
            elif list_type == '30.7ㅋㅋ':
                self.variable_types[var_name] = 'list_float15'
            else:
                # default to string list
                self.variable_types[var_name] = 'list_str'
            self.variables[var_name] = []
            if protected:
                self.protected_vars.add(var_name)
            return True

        # 2. Variable increment/decrement operations
        # [변수명]꿀꺽<밥: +1
        # [변수명]꿀꺽<빵: +0.1
        # [변수명]꿀꺽<고기: +0.01
        # [변수명]꿀꺽<고기고기: +0.001 (pattern continues with repetition)
        # [변수명]꿀꺽<야채: -1
        # [변수명]꿀꺽<설사약: -0.1
        # [변수명]꿀꺽<포자빵: -0.01
        # [변수명]꿀꺽<포자빵포자빵: -0.001 (pattern continues with repetition)
        match_increment = re.match(r'\[(?:\((.+?)\)|(.+?))\]꿀꺽<(.+)', line)
        if match_increment:
            var_name = match_increment.group(1) or match_increment.group(2)
            operation = match_increment.group(3).strip()
            
            if var_name not in self.variables:
                print(f"오류: 정의되지 않은 변수 '{var_name}'")
                sys.exit(1)
            
            # Calculate the increment/decrement value
            delta = 0
            if operation == '밥':
                delta = 1
            elif operation == '빵':
                delta = 0.1
            elif operation.startswith('고기'):
                # Count number of '고기' repetitions
                count = operation.count('고기')
                delta = 0.01 * (0.1 ** (count - 1))
            elif operation == '야채':
                delta = -1
            elif operation == '설사약':
                delta = -0.1
            elif operation.startswith('포자빵'):
                # Count number of '포자빵' repetitions
                count = operation.count('포자빵')
                delta = -0.01 * (0.1 ** (count - 1))
            else:
                print(f"오류: 알 수 없는 연산 '{operation}'")
                sys.exit(1)
            
            # Apply the operation
            var_type = self.variable_types[var_name]
            if var_type in ('int', 'float7', 'float15'):
                self.variables[var_name] += delta
                # Keep type consistency for int
                if var_type == 'int':
                    self.variables[var_name] = int(self.variables[var_name])
            else:
                print(f"오류: '{var_name}' 변수에 대한 꿀꺽 연산은 지원되지 않습니다.")
                sys.exit(1)
            return True

        # 2b. List assignment: [리스트명]쿰척<"[v1,v2,...]"
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
                    elif t == 'list_float7' or t == 'list_float15':
                        parsed.append(float(p))
                    else:
                        parsed.append(p)
                except ValueError:
                    print(f"오류: '{p}'은(는) 리스트 '{var_name}'의 형식에 맞지 않습니다.")
                    sys.exit(1)
            self.variables[var_name] = parsed
            return True

        # 3. Output
        # 줄바꿈 없는 출력: ("문자열")<쿰척, ('변수')<쿰척, ("문자열"쿰척'변수')<쿰척 (Assuming suffix)
        # 줄바꿈 출력: ("")쿰척<쿰척
        
        # Check for newline print first (more specific)
        if line.endswith('쿰척<쿰척'):
            content = line[:-5] # Remove 쿰척<쿰척
            self.handle_print(content, newline=True)
            return True
        elif line.endswith('<쿰척'):
            content = line[:-3] # Remove <쿰척
            self.handle_print(content, newline=False)
            return True

        # 4. Input (Standalone)
        # 쿰척<() or 쿰척<쿰척()
        if line == '쿰척<()':
            input() # Just consume input? Or maybe return it? 
            # The spec says "키보드 입력". Usually this implies waiting for user.
            return True
        if line == '쿰척<쿰척()':
            input()
            print() # Maybe newline after input?
            return True
        
        # 5. Input to Variable
        # 쿰척<(변수명)> -> Input to variable
        # Support 쿰척<(변수명)> or 쿰척<변수명 (if user omits parens, but spec says (변수명))
        match_input_var = re.match(r'쿰척<\((.+?)\)', line)
        if match_input_var:
            var_name = match_input_var.group(1)
            if var_name in self.variables:
                val_str = input()
                try:
                    if self.variable_types[var_name] == 'int':
                        self.variables[var_name] = int(val_str)
                    else:
                        self.variables[var_name] = float(val_str)
                except ValueError:
                    print(f"오류: '{val_str}'은(는) 변수 '{var_name}'에 적합한 값이 아닙니다.")
                    sys.exit(1)
            else:
                print(f"오류: 정의되지 않은 변수 '{var_name}'")
                sys.exit(1)
            return True

        # 6. For loop: 그챼(<init>그챼<cond>그챼<step>)그챼 (followed by 학 on next line)
        match_for = re.match(r'그챼\((.+?)그챼(.+?)그챼(.+?)\)그챼', line)
        if match_for:
            init_stmt = match_for.group(1).strip()
            cond_expr = match_for.group(2).strip()
            step_stmt = match_for.group(3).strip()
            self.in_block = True
            self.block_type = 'for'
            self.block_context = {'init': init_stmt, 'cond': cond_expr, 'step': step_stmt}
            return True
        
        # 7. If statement: 비만인가[조건]알아보자
        match_if = re.match(r'비만인가\[(.+?)\]알아보자', line)
        if match_if:
            cond_expr = match_if.group(1).strip()
            self.in_block = True
            self.block_type = 'if'
            self.block_context = {'cond': cond_expr}
            self.if_condition_met = False
            return True
        
        # 7b. Elseif statement: 학범이는비만일수도있음[조건]
        match_elseif = re.match(r'학범이는비만일수도있음\[(.+?)\]', line)
        if match_elseif:
            cond_expr = match_elseif.group(1).strip()
            self.in_block = True
            self.block_type = 'elseif'
            self.block_context = {'cond': cond_expr}
            return True
        
        # 7c. Else statement: 학범이는비만이아님
        if line == '학범이는비만이아님':
            self.in_block = True
            self.block_type = 'else'
            self.block_context = {}
            return True
        
        # 7d. If block markers
        if line == '학범이는비만임':
            # This is the opening marker for if-true block, skip it
            return True
        
        # 8. While loop: 나살뺄거야(<cond>) (followed by 5분 marker, then body, then 귤한봉지)
        match_while = re.match(r'나살뺄거야\((.+?)\)', line)
        if match_while:
            cond_expr = match_while.group(1).strip()
            self.in_block = True
            self.block_type = 'while'
            self.block_context = {'cond': cond_expr}
            return True
        
        # 8b. Skip 5분 marker (body start for while)
        if line == '5분':
            return True
        
        # 9. Function definition: [funcname]미쉥물 연료[params]전줴
        match_func_def = re.match(r'\[(.+?)\]미쉥물 ?연료\[(.*)\]전줴', line)
        if match_func_def:
            func_name = match_func_def.group(1).strip()
            params_str = match_func_def.group(2).strip()
            params = [p.strip() for p in params_str.split(',')] if params_str else []
            self.in_block = True
            self.block_type = 'function'
            self.block_context = {'name': func_name, 'params': params}
            return True
        
        # 10a. Variable/List reset: 간장먹고[변수명]치기 or 간장먹고[리스트명]치기
        match_reset = re.match(r'간장먹고\[(.+?)\]치기', line)
        if match_reset:
            var_name = match_reset.group(1).strip()
            if var_name not in self.variables:
                print(f"오류: 정의되지 않은 변수 '{var_name}'")
                sys.exit(1)
            var_type = self.variable_types[var_name]
            if var_type == 'int':
                self.variables[var_name] = 30
            elif var_type == 'float7':
                self.variables[var_name] = 30.7
            elif var_type == 'float15':
                self.variables[var_name] = 30.7
            elif var_type.startswith('list'):
                self.variables[var_name] = []
            elif var_type == 'str':
                self.variables[var_name] = ""
            return True
        
        # 10b. Random value assignment: 포자[변수명]
        match_random_var = re.match(r'포자\[(.+?)\]', line)
        if match_random_var:
            var_name = match_random_var.group(1).strip()
            if var_name not in self.variables:
                print(f"오류: 정의되지 않은 변수 '{var_name}'")
                sys.exit(1)
            if var_name in self.protected_vars:
                # Protected variable, skip random assignment
                return True
            self.assign_random_value(var_name)
            return True
        
        # 10c. Random value to all variables: 포자빵
        if line == '포자빵':
            for var_name in self.variables.keys():
                if var_name not in self.protected_vars:
                    self.assign_random_value(var_name)
            return True
        
        # 11. Function call: [funcname]([args])
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
                result = self.call_function(func_name, args)
                # Store result in a temporary location or return it
                # For now, function calls in expressions are not yet supported
                return True
        
        # 12. List element print: [리스트명]쿰척[번호]
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

        return False

    def assign_random_value(self, var_name):
        """Assign a random value to a variable based on its type."""
        var_type = self.variable_types[var_name]
        
        if var_type == 'int':
            self.variables[var_name] = random.randint(-1000, 1000)
        elif var_type == 'float7':
            self.variables[var_name] = random.uniform(-1000.0, 1000.0)
        elif var_type == 'float15':
            self.variables[var_name] = random.uniform(-1000.0, 1000.0)
        elif var_type == 'str':
            # Random string from a set of Korean words
            words = ['학범', '비만', '하악', '귤', '쿰척', '꿀꺽', '포자', '미쉥물']
            self.variables[var_name] = random.choice(words)
        elif var_type.startswith('list_'):
            # Random list with 3-5 elements
            size = random.randint(3, 5)
            if var_type == 'list_int':
                self.variables[var_name] = [random.randint(-100, 100) for _ in range(size)]
            elif var_type in ('list_float7', 'list_float15'):
                self.variables[var_name] = [random.uniform(-100.0, 100.0) for _ in range(size)]
            elif var_type == 'list_str':
                words = ['학범', '비만', '하악', '귤', '쿰척']
                self.variables[var_name] = [random.choice(words) for _ in range(size)]
    
    def call_function(self, func_name, args):
        """Call a function with arguments."""
        if func_name not in self.functions:
            print(f"오류: 정의되지 않은 함수 '{func_name}'")
            sys.exit(1)
        
        params, body = self.functions[func_name]
        
        if len(args) != len(params):
            print(f"오류: 함수 '{func_name}'는 {len(params)}개의 매개변수가 필요하지만 {len(args)}개가 전달되었습니다.")
            sys.exit(1)
        
        # Save current variables (simple scope)
        saved_vars = self.variables.copy()
        saved_types = self.variable_types.copy()
        
        # Set parameters
        for param, arg in zip(params, args):
            # Determine type from arg
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
                self.variable_types[param] = 'list_int'  # default
        
        # Execute function body
        self.return_flag = False
        self.return_value = None
        
        for body_line in body:
            if not self.process_line(body_line):
                print(f"오류: 함수 본문 오류: {body_line}")
                sys.exit(1)
            if self.return_flag:
                break
        
        # Get return value
        result = self.return_value
        
        # Restore variables
        self.variables = saved_vars
        self.variable_types = saved_types
        self.return_flag = False
        self.return_value = None
        
        return result

    def execute_block(self):
        """Execute a block of code (for loop, while loop, function, or if/elseif/else)."""
        if self.block_type == 'function':
            # Store function definition
            func_name = self.block_context['name']
            params = self.block_context['params']
            self.functions[func_name] = (params, self.block_buffer[:])
            return
        
        elif self.block_type == 'if':
            # Execute if block
            cond_expr = self.block_context['cond']
            if self.evaluate_condition(cond_expr):
                self.if_condition_met = True
                for body_line in self.block_buffer:
                    if not self.process_line(body_line):
                        print(f"오류: if문 본문 오류: {body_line}")
                        sys.exit(1)
                    if self.break_flag or self.return_flag:
                        break
            return
        
        elif self.block_type == 'elseif':
            # Execute elseif block only if previous conditions were false
            cond_expr = self.block_context['cond']
            if not self.if_condition_met and self.evaluate_condition(cond_expr):
                self.if_condition_met = True
                for body_line in self.block_buffer:
                    if not self.process_line(body_line):
                        print(f"오류: elseif문 본문 오류: {body_line}")
                        sys.exit(1)
                    if self.break_flag or self.return_flag:
                        break
            return
        
        elif self.block_type == 'else':
            # Execute else block only if no previous conditions were met
            if not self.if_condition_met:
                for body_line in self.block_buffer:
                    if not self.process_line(body_line):
                        print(f"오류: else문 본문 오류: {body_line}")
                        sys.exit(1)
                    if self.break_flag or self.return_flag:
                        break
            # Reset condition flag after else
            self.if_condition_met = False
            return
        
        elif self.block_type == 'for':
            # Execute for loop
            init_stmt = self.block_context['init']
            cond_expr = self.block_context['cond']
            step_stmt = self.block_context['step']
            
            # Execute init
            if not self.process_line(init_stmt):
                print(f"오류: for문 초기화 구문 오류: {init_stmt}")
                sys.exit(1)
            
            # Loop
            max_iterations = 100000  # safety limit
            iterations = 0
            while iterations < max_iterations:
                # Check condition
                if not self.evaluate_condition(cond_expr):
                    break
                
                # Execute body
                self.break_flag = False
                for body_line in self.block_buffer:
                    if not self.process_line(body_line):
                        print(f"오류: for문 본문 오류: {body_line}")
                        sys.exit(1)
                    if self.break_flag:
                        break
                
                # If break was hit, exit outer loop too
                if self.break_flag:
                    self.break_flag = False
                    break
                
                # Execute step
                if not self.process_line(step_stmt):
                    print(f"오류: for문 진행 구문 오류: {step_stmt}")
                    sys.exit(1)
                
                iterations += 1
            
            if iterations >= max_iterations:
                print("오류: for문이 너무 많이 반복되었습니다 (무한 루프?)")
                sys.exit(1)
        
        elif self.block_type == 'while':
            # Execute while loop
            cond_expr = self.block_context['cond']
            
            max_iterations = 100000
            iterations = 0
            while iterations < max_iterations:
                # Check condition
                if not self.evaluate_condition(cond_expr):
                    break
                
                # Execute body
                self.break_flag = False
                for body_line in self.block_buffer:
                    if not self.process_line(body_line):
                        print(f"오류: while문 본문 오류: {body_line}")
                        sys.exit(1)
                    if self.break_flag:
                        break
                
                # If break was hit, exit outer loop too
                if self.break_flag:
                    self.break_flag = False
                    break
                
                iterations += 1
            
            if iterations >= max_iterations:
                print("오류: while문이 너무 많이 반복되었습니다 (무한 루프?)")
                sys.exit(1)

    def evaluate_condition(self, expr):
        """Evaluate a condition expression and return True/False."""
        expr = expr.strip()
        
        # Handle boolean literals
        if expr == '야오루폐':
            return True
        if expr == '야조깜베':
            return False
        
        # Handle comparison operators - Korean keywords
        # Check compound operators first, then simple ones
        korean_ops = [
            ('비만정상', '<='),  # 비만 or 정상 = <=
            ('홀쭉정상', '>='),  # 홀쭉 or 정상 = >=
            ('정상정상', '=='),  # 정상정상 = ==
            ('정상', '=='),     # 정상 = ==
            ('비만', '<'),      # 비만 = <
            ('홀쭉', '>'),      # 홀쭉 = >
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
        
        # If no operator, try to evaluate as expression
        val = self.evaluate_expression(expr)
        # Python-like truthiness
        return bool(val)

    def evaluate_expression(self, expr):
        """Evaluate an expression and return its value."""
        expr = expr.strip()
        
        # Try arithmetic operations FIRST (before checking variable refs)
        # Korean keywords
        # Order matters: check longer operators first to avoid partial matches
        operators = [
            ('비이만하악범', '^'),  # 비이만하악범 = power
            ('학범비만', '*'),  # 학범비만 = multiply
            ('비만학범', '/'),  # 비만학범 = divide
            ('하악범', '+'),  # 하악범 = add
            ('하악버엄', '-'),  # 하악버엄 = subtract
        ]
        
        for korean_op, symbol_op in operators:
            if korean_op in expr:
                parts = expr.split(korean_op, 1)
                if len(parts) == 2:
                    left = self.evaluate_expression(parts[0].strip())
                    right = self.evaluate_expression(parts[1].strip())
                    if symbol_op == '+':
                        return left + right
                    elif symbol_op == '-':
                        return left - right
                    elif symbol_op == '*':
                        return left * right
                    elif symbol_op == '/':
                        return left / right if right != 0 else 0
                    elif symbol_op == '^':
                        return left ** right
        
        # Check if it's a variable reference 'varname'
        if expr.startswith("'") and expr.endswith("'"):
            var_name = expr[1:-1]
            if var_name in self.variables:
                return self.variables[var_name]
            else:
                # Return the variable name as-is for debugging, or raise error
                return 0  # Default for undefined in expression context
        
        # Check if it's a number
        try:
            if '.' in expr:
                return float(expr)
            else:
                return int(expr)
        except ValueError:
            pass
        
        # Check if it's a string literal
        if expr.startswith('"') and expr.endswith('"'):
            return expr[1:-1]
        
        print(f"오류: 표현식을 평가할 수 없습니다: {expr}")
        sys.exit(1)

    def handle_print(self, content_block, newline):
        # content_block is like ("문자열") or ('변수') or ("문자열"쿰척'변수')
        
        if content_block.startswith('(') and content_block.endswith(')'):
            inner = content_block[1:-1]
        else:
            inner = content_block

        # Use regex to find string literals ("...") or variable references ('...')
        # This avoids splitting on '쿰척' if it happens to be inside a string (though unlikely given the syntax)
        # and correctly identifies the tokens.
        tokens = re.findall(r'("[^"]*"|\'[^\']*\'|\[[^\]]+\]\[\d+\])', inner)
        
        output_str = ""
        
        for token in tokens:
            if token.startswith('"') and token.endswith('"'):
                # String literal
                output_str += token[1:-1]
            elif token.startswith("'") and token.endswith("'"):
                # Variable
                var_name = token[1:-1]
                if var_name in self.variables:
                    val = self.variables[var_name]
                    # Format based on type
                    v_type = self.variable_types[var_name]
                    if v_type == 'int':
                        output_str += str(val)
                    elif v_type == 'float7':
                        output_str += f"{val:.7f}"
                    elif v_type == 'float15':
                        output_str += f"{val:.15f}"
                else:
                    output_str += "undefined"
            elif token.startswith('[') and re.match(r'\[[^\]]+\]\[\d+\]', token):
                # list index token like [listname][N]
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

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: python interpreter.py <파일.lhb>")
    else:
        interpreter = HaklangInterpreter()
        interpreter.execute_file(sys.argv[1])
