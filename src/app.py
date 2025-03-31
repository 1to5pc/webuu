from flask import Flask, render_template, request, jsonify
import cope
import io
from contextlib import redirect_stdout
from firebase_config import db

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

def validate_g0_number(g0_number):
    """Validate G0 number format"""
    if not g0_number:
        return False
    return (g0_number.upper().startswith('G0') and 
            len(g0_number) == 6 and 
            g0_number[2:].isdigit())

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
            elif command == "3":
                program_state['current_option'] = "3"
                program_state['waiting_for_input'] = True
                program_state['step'] = 0
                print("Enter your G0 number: ")
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
            elif program_state['current_option'] == "3":
                if program_state['step'] == 0:
                    if validate_g0_number(command):
                        program_state['temp_g0'] = command.upper()
                        program_state['step'] = 1
                        print("Enter your full name: ")
                    else:
                        program_state['waiting_for_input'] = False
                        print("❌ Invalid G0 number format! Should be like G02199")
                elif program_state['step'] == 1:
                    try:
                        db.collection('addMe').document(program_state['temp_g0']).set({
                            'name': command.strip(),
                            'verified': False
                        })
                        print(f"✅ Successfully added {program_state['temp_g0']} with name: {command}")
                        print("Your info will be added to the database shortly.")
                    except Exception as e:
                        print(f"❌ Error saving to database: {str(e)}")
                    program_state['waiting_for_input'] = False
                    del program_state['temp_g0']

    return jsonify({
        "output": output.getvalue(),
        "waiting_for_input": program_state['waiting_for_input']
    })

if __name__ == '__main__':
    app.run(debug=False)