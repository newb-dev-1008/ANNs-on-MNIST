import sys
import string
import os
import argparse

static_base = ''

def main():
    global static_base
    
    commandline_args = parse_commandline()
    
    bootstrap_switch = get_bootstrap_switch(commandline_args)

    path = get_path(commandline_args)
    if path == 'exit':
        return
    
    vm_filenames = get_vm_filenames(path)
    asm_filename = get_asm_filename(vm_filenames[0])   

    with open(asm_filename, 'w') as output:
            
        if bootstrap_switch is True:
            output.write(write_init())
        
        for file in vm_filenames:
        
            with open(file, 'r') as vm:
            
                static_base = os.path.splitext(os.path.basename(file))[0]
                
                for line in vm:
                    line = clean_line(line, ['//'])
                    ct = get_command_type(line)
                    args = get_arguments(line, ct)
                    asm = translate_command(ct, args)
                    if not line:
                        oline = ''
                    else:
                        oline = asm + '\n'
                    output.write(oline)


def parse_commandline():
    parser = argparse.ArgumentParser()
    
    parser.add_argument('inputargument', nargs='?')
    parser.add_argument('-n', action = 'store_false')
    
    args = parser.parse_args()
    
    return args
                    
def get_path(args):
    if(args.inputargument is None):
        print('vmtranslator.py must have a directory name or file name argument.  Type a directory path or .vm file name path as an argument.')
        return 'exit'
        
    path = os.path.abspath(args.inputargument)

    if(not os.path.exists(path)):
        print("The directory or file to translate does not exist.  Try another directory or file path.")
        return 'exit'
        
    return path
    
def get_bootstrap_switch(args):
    return args.n
    
def get_vm_filenames(path):
    vm_filenames = []
    if(os.path.isdir(path)):
        for file in os.listdir(path):
            if file.endswith(".vm"):
                vm_filenames.append(os.path.join(path, file))
        if not vm_filenames:
            print("If a directory is used as an argument it must contain at least one .vm file.  Try another directory or file path.")
            return
    else:
        if not path.endswith(".vm"):
            print("vmtranslator.py only works on .vm files.  Try another path argument.")
            return
        else:
            vm_filenames.append(path)
    return vm_filenames

def get_asm_filename(vm_filename):
    return os.path.join(os.path.dirname(vm_filename), "//", os.path.split(os.path.dirname(vm_filename))[1], '.asm')

   
def clean_line(line, sep):
    for s in sep:
        line = line.split(s)[0]
    return line.strip()
            
def get_command_type(line):
    line3 = line[0:3]
    if line3 in ['']:
        return ''
    elif line3 in ['pus']:
        return 'C_PUSH'
    elif line3 in ['pop']:
        return 'C_POP'        
    elif line3 in ['lab']:
        return 'C_LABEL'
    elif line3 in ['got']:
        return 'C_GOTO'
    elif line3 in ['if-']:
        return 'C_IF'
    elif line3 in ['fun']:
        return 'C_FUNCTION'
    elif line3 in ['cal']:
        return 'C_CALL'
    elif line3 in ['ret']:
        return 'C_RETURN'
    else:
        return 'C_ARITHMETIC'
        
def get_arguments(line, ct):
    if ct == 'C_ARITHMETIC':
        return line
    elif ct=='C_LABEL' or ct=='C_GOTO' or ct=='C_IF':
        return line.split()[1]
    elif ct=='C_PUSH' or ct=='C_POP' or ct=='C_FUNCTION' or ct=='C_CALL':
        return line.split()[1:3]
    else: #C_RETURN
        return ''
    
def translate_command(ct, args):
    if   ct == '':
        asm = ''
    elif ct == 'C_ARITHMETIC':
        asm = write_arithmetic(args)
    elif ct == 'C_PUSH':
        asm = write_push(*args)
    elif ct == 'C_POP':
        asm = write_pop(*args)
    elif ct == 'C_LABEL':
        asm = write_label(args)
    elif ct == 'C_GOTO':
        asm = write_goto(args)
    elif ct == 'C_IF':
        asm = write_ifgoto(args)
    elif ct == 'C_CALL':
        asm = write_call(*args)
    elif ct == 'C_FUNCTION':
        asm = write_function(*args)
    elif ct == 'C_RETURN':
        asm = write_return()
    return asm
       
def write_init():
    asm = ('@256' + '\n' +                      
           'D=A'  + '\n' +
           '@SP'  + '\n' +
           'M=D'  + '\n' +
           write_call('Sys.init','0') + '\n')   
    return asm

def write_arithmetic(command):
    if "counter_eq" not in write_arithmetic.__dict__:
        write_arithmetic.counter_eq = 0
        write_arithmetic.counter_gt = 0
        write_arithmetic.counter_lt = 0
        
    if command == 'add':
        asm = ('@SP'   + '\n' + 
               'M=M-1' + '\n' +
               'A=M'   + '\n' +
               'D=M'   + '\n' +
               'A=A-1' + '\n' + 
               'M=D+M')         
    elif command == 'sub':
        asm = ('@SP'   + '\n' + 
               'M=M-1' + '\n' +
               'A=M'   + '\n' +
               'D=M'   + '\n' +
               'A=A-1' + '\n' + 
               'M=M-D')         
    elif command == 'neg':
        asm = ('@SP'   + '\n' +
               'M=M-1' + '\n' +
               'A=M'   + '\n' +
               'M=-M'  + '\n' + 
               '@SP'   + '\n' +
               'M=M+1')
    elif command == 'eq':
        asm = ('@SP'      + '\n' +                              
               'M=M-1'    + '\n' +
               'A=M'      + '\n' +
               'D=M'      + '\n' +
               'A=A-1'    + '\n' +                              
               'D=M-D'    + '\n' +                              
               '@EQTRUE'  + str(write_arithmetic.counter_eq) + '\n' +          
               'D;JEQ'    + '\n' +
               '@SP'      + '\n' +                               
               'A=M-1'    + '\n' +
               'M=0'      + '\n' +
               '@EQEND'   + str(write_arithmetic.counter_eq) + '\n' + 
               '0;JMP'    + '\n' +
               '(EQTRUE'  + str(write_arithmetic.counter_eq) + ')' + '\n' + 
               '@SP'      + '\n' +                              
               'A=M-1'    + '\n' + 
               'M=-1'     + '\n' + 
               '(EQEND'   + str(write_arithmetic.counter_eq) + ')')
        write_arithmetic.counter_eq += 1
    elif command == 'gt':
        asm = ('@SP'      + '\n' +                              
               'M=M-1'    + '\n' +
               'A=M'      + '\n' +
               'D=M'      + '\n' +
               'A=A-1'    + '\n' +                              
               'D=M-D'    + '\n' +                              
               '@GTTRUE'  + str(write_arithmetic.counter_gt) + '\n' +          
               'D;JGT'    + '\n' +
               '@SP'      + '\n' +                              
               'A=M-1'    + '\n' +
               'M=0'      + '\n' +
               '@GTEND'   + str(write_arithmetic.counter_gt) + '\n' +
               '0;JMP'    + '\n' +
               '(GTTRUE'  + str(write_arithmetic.counter_gt) + ')' + '\n' + 
               '@SP'      + '\n' +                              
               'A=M-1'    + '\n' + 
               'M=-1'     + '\n' + 
               '(GTEND'   + str(write_arithmetic.counter_gt) + ')')
        write_arithmetic.counter_gt += 1
    elif command == 'lt':
        asm = ('@SP'      + '\n' +                              
               'M=M-1'    + '\n' +
               'A=M'      + '\n' +
               'D=M'      + '\n' +
               'A=A-1'    + '\n' +                              
               'D=M-D'    + '\n' +                              
               '@LTTRUE'  + str(write_arithmetic.counter_lt) + '\n' +          
               'D;JLT'    + '\n' +
               '@SP'      + '\n' +                              
               'A=M-1'    + '\n' +
               'M=0'      + '\n' +
               '@LTEND'   + str(write_arithmetic.counter_lt) + '\n' +
               '0;JMP'    + '\n' +
               '(LTTRUE'  + str(write_arithmetic.counter_lt) + ')' + '\n' + 
               '@SP'      + '\n' +                              
               'A=M-1'    + '\n' + 
               'M=-1'     + '\n' + 
               '(LTEND'   + str(write_arithmetic.counter_lt) + ')' )
        write_arithmetic.counter_lt += 1
    elif command == 'and':
        asm = ('@SP'   + '\n' + 
               'M=M-1' + '\n' +
               'A=M'   + '\n' +
               'D=M'   + '\n' +
               'A=A-1' + '\n' + 
               'M=D&M')         
    elif command == 'or':
        asm = ('@SP'   + '\n' + 
               'M=M-1' + '\n' +
               'A=M'   + '\n' +
               'D=M'   + '\n' +
               'A=A-1' + '\n' + 
               'M=D|M')         
    elif command == 'not':
        asm = ('@SP'   + '\n' +
               'M=M-1' + '\n' +
               'A=M'   + '\n' +
               'M=!M'  + '\n' + 
               '@SP'   + '\n' +
               'M=M+1')
    return asm

def write_push(segment, index):
    if segment == 'constant':
        asm = ('@' + index + '\n' +   
               'D=A' + '\n' +         
               '@SP' + '\n' +         
               'A=M' + '\n' +         
               'M=D' + '\n' +         
               '@SP' + '\n' +         
               'M=M+1')
    elif segment == 'local':
        asm = ('@LCL'  + '\n' +           
               'D=M'   + '\n' +
               '@'     + index + '\n' +
               'A=D+A' + '\n' +
               'D=M'   + '\n' +
               '@SP'   + '\n' +           
               'A=M'   + '\n' + 
               'M=D'   + '\n' +
               '@SP'   + '\n' +         
               'M=M+1')
    elif segment == 'argument':
        asm = ('@ARG'  + '\n' +           
               'D=M'   + '\n' +
               '@'     + index + '\n' +
               'A=D+A' + '\n' +
               'D=M'   + '\n' +
               '@SP'   + '\n' +           
               'A=M'   + '\n' + 
               'M=D'   + '\n' +
               '@SP'   + '\n' +           
               'M=M+1')
    elif segment == 'this':
        asm = ('@THIS'  + '\n' +           
               'D=M'   + '\n' +
               '@'     + index + '\n' +
               'A=D+A' + '\n' +
               'D=M'   + '\n' +
               '@SP'   + '\n' +           
               'A=M'   + '\n' + 
               'M=D'   + '\n' +
               '@SP'   + '\n' +           
               'M=M+1')
    elif segment == 'that':
        asm = ('@THAT'  + '\n' +           
               'D=M'   + '\n' +
               '@'     + index + '\n' +
               'A=D+A' + '\n' +
               'D=M'   + '\n' +
               '@SP'   + '\n' +           
               'A=M'   + '\n' + 
               'M=D'   + '\n' +
               '@SP'   + '\n' +           
               'M=M+1')
    elif segment == 'pointer':
        asm = ('@R3'  + '\n' +            
               'D=A'   + '\n' +
               '@'     + index + '\n' +
               'A=D+A' + '\n' +
               'D=M'   + '\n' +
               '@SP'   + '\n' +           
               'A=M'   + '\n' + 
               'M=D'   + '\n' +
               '@SP'   + '\n' +           
               'M=M+1')
    elif segment == 'temp':
        asm = ('@R5'  + '\n' +            
               'D=A'   + '\n' +
               '@'     + index + '\n' +
               'A=D+A' + '\n' +
               'D=M'   + '\n' +
               '@SP'   + '\n' +            
               'A=M'   + '\n' + 
               'M=D'   + '\n' +
               '@SP'   + '\n' +           
               'M=M+1')
    elif segment == 'static':
        asm = ('@' + static_base + '.' + index + '\n' + 
               'D=M' + '\n' +
               '@SP' + '\n' +         
               'A=M' + '\n' +         
               'M=D' + '\n' +                             
               '@SP' + '\n' +                             
               'M=M+1')
    return asm

def write_pop(segment, index):
    if segment == 'constant':
        asm = ('@SP' + '\n' +             
               'M=M-1')
    elif segment == 'local':
        asm = ('@LCL'  + '\n' +           
               'D=M'   + '\n' +
               '@'     + index + '\n' +
               'D=D+A' + '\n' +
               '@R13'  + '\n' +
               'M=D'   + '\n' +
               '@SP'   + '\n' +           
               'M=M-1' + '\n' + 
               'A=M'   + '\n' + 
               'D=M'   + '\n' + 
               '@R13'  + '\n' +           
               'A=M'   + '\n' + 
               'M=D')
    elif segment == 'argument':
        asm = ('@ARG'  + '\n' +           
               'D=M'   + '\n' +
               '@'     + index + '\n' +
               'D=D+A' + '\n' +
               '@R13'  + '\n' +
               'M=D'   + '\n' +
               '@SP'   + '\n' +           
               'M=M-1' + '\n' + 
               'A=M'   + '\n' + 
               'D=M'   + '\n' + 
               '@R13'  + '\n' +           
               'A=M'   + '\n' + 
               'M=D')
    elif segment == 'this':
        asm = ('@THIS'  + '\n' +          
               'D=M'   + '\n' +
               '@'     + index + '\n' +
               'D=D+A' + '\n' +
               '@R13'  + '\n' +
               'M=D'   + '\n' +
               '@SP'   + '\n' +           
               'M=M-1' + '\n' + 
               'A=M'   + '\n' + 
               'D=M'   + '\n' + 
               '@R13'  + '\n' +           
               'A=M'   + '\n' + 
               'M=D')
    elif segment == 'that':
        asm = ('@THAT'  + '\n' +          
               'D=M'   + '\n' +
               '@'     + index + '\n' +
               'D=D+A' + '\n' +
               '@R13'  + '\n' +
               'M=D'   + '\n' +
               '@SP'   + '\n' +           
               'M=M-1' + '\n' + 
               'A=M'   + '\n' + 
               'D=M'   + '\n' + 
               '@R13'  + '\n' +           
               'A=M'   + '\n' + 
               'M=D')
    elif segment == 'pointer':
        asm = ('@R3'  + '\n' +            
               'D=A'   + '\n' +
               '@'     + index + '\n' +
               'D=D+A' + '\n' +
               '@R13'  + '\n' +
               'M=D'   + '\n' +
               '@SP'   + '\n' +           
               'M=M-1' + '\n' + 
               'A=M'   + '\n' + 
               'D=M'   + '\n' + 
               '@R13'  + '\n' +           
               'A=M'   + '\n' + 
               'M=D')
    elif segment == 'temp':
        asm = ('@R5'  + '\n' +            
               'D=A'   + '\n' +
               '@'     + index + '\n' +
               'D=D+A' + '\n' +
               '@R13'  + '\n' +
               'M=D'   + '\n' +
               '@SP'   + '\n' +           
               'M=M-1' + '\n' + 
               'A=M'   + '\n' + 
               'D=M'   + '\n' + 
               '@R13'  + '\n' +           
               'A=M'   + '\n' + 
               'M=D')          
    elif segment == 'static':
        asm = ('@SP'   + '\n' +                                     
               'M=M-1' + '\n' + 
               'A=M'   + '\n' + 
               'D=M'   + '\n' + 
               '@' + static_base + '.' + index + '\n' +           
               'M=D')
    return asm
               
def write_label(label):
    asm = '(' + label + ')'
    return asm

def write_goto(label):
    asm = ( '@' + label + '\n' +
            '0;JMP')
    return asm
    
def write_ifgoto(label):

    asm = ('@SP'      + '\n' +          
           'M=M-1'    + '\n' +
           'A=M'      + '\n' +
           'D=M'      + '\n' +
           '@' + label + '\n' +          
           'D;JNE')
    return asm       
               
def write_call(functionName, numArgs):
    if "counter" not in write_call.__dict__:
        write_call.counter = 0
    
    asm = ( '@' + functionName + '.RETURN' + str(write_call.counter) + '\n' + 
            'D=A'   + '\n' +
            '@SP'   + '\n' +         
            'A=M'   + '\n' +         
            'M=D'   + '\n' +                            
            '@SP'   + '\n' +                             
            'M=M+1' + '\n' +
            
            '@LCL'  + '\n' +            
            'D=M'   + '\n' +
            '@SP'   + '\n' +         
            'A=M'   + '\n' +         
            'M=D'   + '\n' +                             
            '@SP'   + '\n' +                           
            'M=M+1' + '\n' +
            
            '@ARG'  + '\n' +            
            'D=M'   + '\n' +
            '@SP'   + '\n' +         
            'A=M'   + '\n' +         
            'M=D'   + '\n' +                           
            '@SP'   + '\n' +                          
            'M=M+1' + '\n' +
            
            '@THIS' + '\n' +            
            'D=M'   + '\n' +
            '@SP'   + '\n' +         
            'A=M'   + '\n' +         
            'M=D'   + '\n' +                   
            '@SP'   + '\n' +                       
            'M=M+1' + '\n' +
            
            '@THAT' + '\n' +            
            'D=M'   + '\n' +
            '@SP'   + '\n' +         
            'A=M'   + '\n' +         
            'M=D'   + '\n' +                           
            '@SP'   + '\n' +                    
            'M=M+1' + '\n' +
            
            '@SP'   + '\n' +           
            'D=M'   + '\n' +
            '@'     + numArgs + '\n' +
            'D=D-A' + '\n' +
            '@5'    + '\n' +
            'D=D-A' + '\n' +
            '@ARG'  + '\n' +           
            'M=D'   + '\n' +
            
            '@SP'   + '\n' +           
            'D=M'   + '\n' +
            '@LCL'  + '\n' +           
            'M=D'   + '\n' +
            
            '@' + functionName + '\n' +   
            '0;JMP' + '\n' +
            
            '(' + functionName + '.RETURN' + str(write_call.counter) + ')')   
            
    write_call.counter += 1
    
    return asm

def write_function(functionName, numLocals):

    asm = ('(' + functionName + ')' + '\n' + 
    
           '@' + numLocals + '\n' +                 
           'D=A'   + '\n' +
           '@' + functionName + '.kcnt' + '\n' +
           'M=D'   + '\n' +
           
           '(' + functionName + '.kloop)' + '\n' +
           
           '@' + functionName + '.kcnt' + '\n' +		
           'D=M'   + '\n' + 
           '@' + functionName + '.END' + '\n' +
           'D;JLE' + '\n' +
            
           '@0'    + '\n' +         
           'D=A'   + '\n' +         
           '@SP'   + '\n' +         
           'A=M'   + '\n' +         
           'M=D'   + '\n' +         
           '@SP'   + '\n' +         
           'M=M+1' + '\n' +
           
           '@' + functionName + '.kcnt' + '\n' +    
           'M=M-1' + '\n' +
            
           '@' + functionName + '.kloop' + '\n' +	
           '0;JMP' + '\n' +
           '(' + functionName + '.END)')
    return asm

def write_return():
    '''Translates return vm command to assembly code'''

    asm = ( '@LCL'   + '\n' +           
            'D=M'    + '\n' +
            '@FRAME' + '\n' +
            'M=D'    + '\n' +
            
            # RET = *(FRAME-5)  
            '@FRAME' + '\n' +           
            'D=M'    + '\n' +
            '@5'     + '\n' +
            'D=D-A'  + '\n' +
            'A=D'    + '\n' +
            'D=M'    + '\n' +
            '@RET'   + '\n' +           
            'M=D'    + '\n' +
            
            #*ARG = pop()
            '@SP'   + '\n' +           
            'M=M-1' + '\n' + 
            'A=M'   + '\n' + 
            'D=M'   + '\n' + 
            '@ARG'  + '\n' +           
            'A=M'   + '\n' + 
            'M=D'   + '\n' +
             
            '@ARG'  + '\n' +            
            'D=M'   + '\n' +
            '@SP'   + '\n' +
            'M=D+1' + '\n' +
            
            '@FRAME' + '\n' +           
            'M=M-1'  + '\n' +
            'A=M'    + '\n' +
            'D=M'    + '\n' +
            '@THAT'  + '\n' +
            'M=D'    + '\n' +
            
            '@FRAME' + '\n' +           
            'M=M-1'  + '\n' +
            'A=M'    + '\n' +
            'D=M'    + '\n' +
            '@THIS'  + '\n' +
            'M=D'    + '\n' +
            
            '@FRAME' + '\n' +           
            'M=M-1'  + '\n' +
            'A=M'    + '\n' +
            'D=M'    + '\n' +
            '@ARG'   + '\n' +
            'M=D'    + '\n' +
            
            '@FRAME' + '\n' +           
            'M=M-1'  + '\n' +
            'A=M'    + '\n' +
            'D=M'    + '\n' +
            '@LCL'   + '\n' +
            'M=D'    + '\n' +
            
            '@RET' + '\n' +
            'A=M'  + '\n' +
            '0;JMP'
           )
    return asm

if __name__ == '__main__':
    sys.exit(main())
