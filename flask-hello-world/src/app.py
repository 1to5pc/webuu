from flask import Flask, render_template, request, jsonify
import cope
import io
from contextlib import redirect_stdout

app = Flask(__name__)
program_state = {
    'waiting_for_input': False,
    'current_option': None,
    'step': 0,
    'student_names': None,
    'initialized': False  # Track initialization state
}

# Load student names before each request
@app.before_request
def initialize():
    global program_state
    if not program_state['initialized']:
        program_state['student_names'] = cope.load_student_names()
        program_state['initialized'] = True

@app.route('/')
def index():
    return render_template('terminal.html')

@app.route('/execute', methods=['POST'])
def execute_command():
    global program_state
    command = request.json.get('command')
    output = io.StringIO()
    
    with redirect_stdout(output):
        if not program_state['waiting_for_input']:
            if command == "0":
                program_state['current_option'] = "0"
                program_state['waiting_for_input'] = True
                program_state['step'] = 0
                print("Enter G0-number or name (e.g., G02199 or Name): ")
            elif command == "1":
                program_state['current_option'] = "1"
                program_state['waiting_for_input'] = True
                program_state['step'] = 0
                print("Enter first G0-number or name: ")
            elif command == "2":
                return jsonify({
                    "output": "Adios, Amigos! 👋", 
                    "reload": True
                })
            else:
                print("Invalid command!")
        else:
            if program_state['current_option'] == "0":
                result = cope.handle_single_input(command, program_state['student_names'])
                program_state['waiting_for_input'] = False
                print(result)
            elif program_state['current_option'] == "1":
                if program_state['step'] == 0:
                    result = cope.handle_first_input(command, program_state['student_names'])
                    program_state['step'] = 1
                    print("\nEnter second G0-number or name: ")
                else:
                    result = cope.handle_second_input(command, program_state['student_names'])
                    program_state['waiting_for_input'] = False
                    print(result)
    
    return jsonify({
        "output": output.getvalue(),
        "waiting_for_input": program_state['waiting_for_input']
    })

if __name__ == '__main__':
    app.run(debug=False)