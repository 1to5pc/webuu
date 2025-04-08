from flask import Flask, render_template, request, jsonify
import cope
import io
import os
from contextlib import redirect_stdout

cred_path = '/etc/secrets/firebase_credentials.json' if "RENDER" in os.environ else os.path.join(os.path.dirname(__file__), '../firebase_credentials.json')
if os.path.exists(cred_path):
    from firebase_config import db

app = Flask(__name__)
program_state = {
    'waiting_for_input': False,
    'current_option': None,
    'step': 0,
    'student_names': None,
    'initialized': False,  # Track initialization state
    'matched_names': None,  # Add this to store matched names
    'current_search': None  # Add this to store current search context
}

# Load student names before each request
@app.before_request
def initialize():
    global program_state
    if not program_state['initialized']:
        # Check if Firebase credentials exist
        if not os.path.exists(cred_path):
            print("⚠️ Firebase credentials not found. Some features may be unavailable.")
            program_state['student_names'] = {}
        else:
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
    command = request.json.get('command').strip()
    output = io.StringIO()
    
    with redirect_stdout(output):
        if program_state.get('matched_names'):  # Handle multiple match selection
            try:
                choice = int(command)
                if choice == -1:
                    program_state['matched_names'] = None
                    program_state['waiting_for_input'] = True
                    print(f"Enter {program_state['current_search']}: ")
                    return jsonify({
                        "output": output.getvalue(),
                        "waiting_for_input": True
                    })
                
                if 0 <= choice < len(program_state['matched_names']):
                    selected_name = program_state['matched_names'][choice]
                    selected_g0 = program_state['student_names'][selected_name]
                    program_state['matched_names'] = None
                    
                    # Handle the selection based on current context
                    if program_state['current_option'] == "0":
                        result = cope.handle_single_input(selected_g0, program_state['student_names'])
                        program_state['waiting_for_input'] = False
                        print(result)
                    elif program_state['current_option'] == "1":
                        if program_state['step'] == 0:
                            result = cope.handle_first_input(selected_g0, program_state['student_names'])
                            program_state['step'] = 1
                            print("\nEnter second G0-number or name: ")
                        else:
                            result = cope.handle_second_input(selected_g0, program_state['student_names'])
                            program_state['waiting_for_input'] = False
                            print(result)
                else:
                    print("Invalid selection number")
                    print("\nEnter number to select (or -1 to search again): ")
                    return jsonify({
                        "output": output.getvalue(),
                        "waiting_for_input": True
                    })
            except ValueError:
                print("Please enter a valid number")
                print("\nEnter number to select (or -1 to search again): ")
                return jsonify({
                    "output": output.getvalue(),
                    "waiting_for_input": True
                })
        elif not program_state['waiting_for_input']:
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
                if not os.path.exists(cred_path):
                    print("\n⚠️ Firebase connection failed: credentials not found")
                    program_state['waiting_for_input'] = False
                else:
                    program_state['current_option'] = "3"
                    program_state['waiting_for_input'] = True
                    program_state['step'] = 0
                    print("Enter your G0 number: ")
            else:
                print("Invalid command!")
        else:
            if program_state['current_option'] == "0":
                result, message = cope.handle_name_search(command, program_state['student_names'])
                if isinstance(result, list):  # Multiple matches found
                    program_state['matched_names'] = result
                    program_state['current_search'] = "G0-number or name"
                    print(message)
                    print("\nEnter number to select (or -1 to search again): ")
                else:
                    program_state['waiting_for_input'] = False
                    if result:
                        print(cope.handle_single_input(result, program_state['student_names']))
                    else:
                        print(message)
            elif program_state['current_option'] == "1":
                if program_state['step'] == 0:
                    result, message = cope.handle_name_search(command, program_state['student_names'])
                    if isinstance(result, list):  # Multiple matches found
                        program_state['matched_names'] = result
                        program_state['current_search'] = "first G0-number or name"
                        print(message)
                        print("\nEnter number to select (or -1 to search again): ")
                    else:
                        program_state['step'] = 1
                        if result:
                            print(cope.handle_first_input(result, program_state['student_names']))
                            print("\nEnter second G0-number or name: ")
                        else:
                            print(message)
                else:
                    result, message = cope.handle_name_search(command, program_state['student_names'])
                    if isinstance(result, list):  # Multiple matches found
                        program_state['matched_names'] = result
                        program_state['current_search'] = "second G0-number or name"
                        print(message)
                        print("\nEnter number to select (or -1 to search again): ")
                    else:
                        program_state['waiting_for_input'] = False
                        if result:
                            print(cope.handle_second_input(result, program_state['student_names']))
                        else:
                            print(message)
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
                        db.collection('studz').document(program_state['temp_g0']).set({
                            'name': command.strip(),
                            'verified': False
                        })
                        print(f"✅ Successfully added {program_state['temp_g0']} with name: {command}")
                        print("Your info will be added to the database shortly.")
                        print("Refresh the page to find yourself in the name list.")
                    except Exception as e:
                        print(f"❌ Error saving to database: {str(e)}")
                    program_state['waiting_for_input'] = False
                    del program_state['temp_g0']

    return jsonify({
        "output": output.getvalue(),
        "waiting_for_input": program_state['waiting_for_input'] or program_state.get('matched_names') is not None
    })

@app.route('/reset', methods=['POST'])
def reset_state():
    global program_state
    program_state = {
        'waiting_for_input': False,
        'current_option': None,
        'step': 0,
        'student_names': None,
        'initialized': False,
        'matched_names': None,
        'current_search': None
    }
    return jsonify({"status": "success"})

if __name__ == '__main__':
    app.run(debug=False)