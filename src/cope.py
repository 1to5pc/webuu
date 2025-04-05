import requests
from bs4 import BeautifulSoup
import json
import random
import os

cred_path = '/etc/secrets/firebase_credentials.json' if "RENDER" in os.environ else os.path.join(os.path.dirname(__file__), '../firebase_credentials.json')
if os.path.exists(cred_path):
    from firebase_config import db

# Global variables and configurations
BASE_URL = "http://220.247.238.114/lg_report"
URLS = {
    'login': f"{BASE_URL}/login",
    'dashboard': f"{BASE_URL}/welcome/dashboard",
    'exam': f"{BASE_URL}/loadExam",
    'marks': f"{BASE_URL}/getStudentMarkRemarks",
    'sports': f"{BASE_URL}/getStudentSportMarkRemarks"
}

def load_student_names():
    """Load student names from Firestore"""
    if not os.path.exists(cred_path):
        print("⚠️ Firebase credentials not found. Name search is unavailable.")
        return {}
        
    try:
        student_names = {}
        docs = db.collection('studz').stream()
        
        for doc in docs:
            g_number = doc.id
            name = doc.get('name')
            if name:
                student_names[name] = g_number
                
        if not student_names:
            print("⚠️ Warning: No student data found in Firestore.")
            return {}
            
        return student_names
    except Exception as e:
        print(f"⚠️ Error accessing Firestore: {e}")
        return {}

def check_input(input_text):
    """
    Check if input is G0-number or name search
    Returns: (type, value)
    type: 'g0' for G0-number, 'name' for name search
    """
    input_text = input_text.strip().upper()
    
    # Check if it's a valid G0 number format
    if (input_text.startswith('G') and len(input_text) == 6 and 
        input_text[1:].isdigit()):
        return ('g0', input_text)
    
    # If contains digits, probably trying G0 number
    if any(char.isdigit() for char in input_text):
        return ('invalid_g0', None)
    
    # Otherwise assume it's a name search
    return ('name', input_text)

def handle_multiple_matches(matched_names, student_names):
    """Handle multiple name matches and return selected G0 number"""
    formatted_matches = []
    for i, name in enumerate(matched_names):
        formatted_matches.append(f"[{i}] {name} ({student_names[name]})")
    return "\n".join(formatted_matches)

def handle_name_search(value, student_names):
    """Handle name search logic"""
    if not student_names:
        return None, "❌ Name search unavailable Firebase connection failed"
    
    # Check if input is a G0 number
    if check_input(value)[0] == "g0":
        return value, None
      
    matched_names = [name for name in student_names.keys() 
                    if any(part.lower() in name.lower() 
                          for part in value.split())]
    
    if not matched_names:
        return None, "❌ No matching names found"
    
    if len(matched_names) == 1:
        return student_names[matched_names[0]], None
    
    # Multiple matches found
    return matched_names, handle_multiple_matches(matched_names, student_names)

def get_user_input(prompt, student_names):
    """Handle user input for G0 number or name"""
    while True:
        user_input = input(prompt)
        input_type, value = check_input(user_input)
        
        if input_type == 'g0':
            return value
        elif input_type == 'name':
            result, message = handle_name_search(value, student_names)
            if isinstance(result, list):  # Multiple matches
                print(message)
                while True:
                    try:
                        choice = int(input("\nEnter number to select (or -1 to search again): "))
                        if choice == -1:
                            break
                        if 0 <= choice < len(result):
                            return student_names[result[choice]]
                        print("Invalid selection number")
                    except ValueError:
                        print("Please enter a valid number")
            elif result:
                return result
            else:
                print(message)
        else:
            print("❌ Invalid G0-number format. Should be like G02199")

def check_website(url):
    """Check if the website is reachable"""
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()  # Raise an error for bad responses (4xx, 5xx)
        print(f"🌐 Website is reachable!")
    except requests.RequestException:
        print(f"📵 Failed to reach website")
        exit()

def scrape_student_data(credentials):
    """
    Scrape student data using provided credentials and return raw JSON data
    
    Args:
        credentials (dict): Dictionary containing user_email and password
    
    Returns:
        dict: JSON data containing all student information
    """
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:114.0) Gecko/20100101 Firefox/114.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7; rv:114.0) Gecko/20100101 Firefox/114.0",
        "Mozilla/5.0 (X11; Linux x86_64; rv:114.0) Gecko/20100101 Firefox/114.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/114.0.1823.67",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Mobile Safari/537.36",
        "Mozilla/5.0 (iPad; CPU OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59"
    ]
    session = requests.Session()
    data = {
        "success": False,
        "student_name": None,
        "exam_data": None,
        "marks_data": None,
        "sports_data": None
    }

    try:
        random_user_agent = random.choice(user_agents)
        headers = {
            "User-Agent": random_user_agent,
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "http://220.247.238.114",
            "Referer": "http://220.247.238.114/lg_report/welcome/login",
            "Connection": "keep-alive"
        }

        response = session.post(URLS['login'], data=credentials, headers=headers)
        if "Email or Password is Wrong" in response.text:
            print("❌ Login Failed for:", credentials["user_email"])
            return data

        data["success"] = True

        dashboard_response = session.get(URLS['dashboard'], headers=headers)
        dashboard_soup = BeautifulSoup(dashboard_response.text, "html.parser")
        name_surname = dashboard_soup.find("span", class_="badge", string=True)
        if name_surname:
            data["student_name"] = name_surname.text.strip()
            print("✔️ Login Successful for:", name_surname.text.strip())

        exam_response = session.get(URLS['exam'], headers=headers)
        try:
            data["exam_data"] = json.loads(exam_response.text)
        except json.JSONDecodeError:
            data["exam_data"] = None

        marks_response = session.post(URLS['marks'], headers=headers)
        try:
            data["marks_data"] = json.loads(marks_response.text)
        except json.JSONDecodeError:
            data["marks_data"] = None

        sports_response = session.post(URLS['sports'], headers=headers)
        try:
            data["sports_data"] = json.loads(sports_response.text)
        except json.JSONDecodeError:
            data["sports_data"] = None

    except Exception as e:
        data["error"] = str(e)
    finally:
        session.close()
        return data

def extract_marks(data):
    """
    Extract and format marks from raw JSON data
    
    Args:
        data (dict): Raw JSON data from scrape_student_data()
    
    Returns:
        tuple: (subject_marks, sports_marks) dictionaries
    """
    subject_marks = {}
    if data.get('marks_data'):
        for mark in data['marks_data']:
            subject_marks[mark['subject']] = {
                'mark': mark['mark'],
                'remark': mark['remark'],
                'teacher': mark['teacher']
            }
    
    sports_marks = {}
    if data.get('sports_data'):
        for sport in data['sports_data']:
            sports_marks[sport['sport']] = {
                'mark': sport['mark'],
                'activity_type': 'Physical' if sport['activity'] == 'physical' else 'Non-Physical',
                'participation': 'Physical Training' if sport['type'] == 'pt' else 'Extra Curricular'
            }
    
    return subject_marks, sports_marks, data.get('student_name')

def display_single_user_stats(name, subjects, sports):
    """Display stats for a single user"""
    print(f"\n👤 Student Name: {name}")

    print("\n📚 Subject Marks:")
    for subject, details in subjects.items():
        print(f"{subject}: {details['mark']} - {details['remark']} (Teacher: {details['teacher']})")

    print("\n🏆 Sports Marks:")
    for sport, details in sports.items():
        print(f"{sport}: {details['mark']} ({details['activity_type']}, {details['participation']})")

def compare(subjects1, sports1, subjects2, sports2, user1, user2):
    """
    Compare two sets of marks and print differences
    
    Args:
        subjects1 (dict): Subject marks for user 1
        sports1 (dict): Sports marks for user 1
        subjects2 (dict): Subject marks for user 2
        sports2 (dict): Sports marks for user 2
    """
    print("\n📚 Subject Marks Comparison:")
    for subject in subjects1.keys():
        if subject in subjects2:
            mark1 = int(subjects1[subject]['mark'])
            mark2 = int(subjects2[subject]['mark'])
            if mark1 > mark2:
                print(f"{subject}: {mark1} vs {mark2} ({user1} performed better)")
            elif mark1 < mark2:
                print(f"{subject}: {mark1} vs {mark2} ({user2} performed better)")
            else:
                print(f"{subject}: {mark1} vs {mark2} (Equal performance)")
        else:
            print(f"{subject} unique to {user1} with mark: {subjects1[subject]['mark']}")

    for subject in subjects2.keys():
        if subject not in subjects1:
            print(f"{subject} unique to {user2} with mark: {subjects2[subject]['mark']}")

    print("\n🏆 Sports Marks Comparison:")
    for sport in sports1.keys():
        if sport in sports2:
            mark1 = int(sports1[sport]['mark'])
            mark2 = int(sports2[sport]['mark'])
            if mark1 > mark2:
                print(f"{sport}: {mark1} vs {mark2} ({user1} performed better)")
            elif mark1 < mark2:
                print(f"{sport}: {mark1} vs {mark2} ({user2} performed better)")
            else:
                print(f"{sport}: {mark1} vs {mark2} (Equal performance)")
        else:
            print(f"{sport} unique to {user1} with mark: {sports1[sport]['mark']}")

    for sport in sports2.keys():
        if sport not in sports1:
            print(f"{sport} unique to {user2} with mark: {sports2[sport]['mark']}")

def handle_single_input(command, student_names):
    """Handle input for single user mode"""
    input_type, value = check_input(command)
    if input_type == 'g0':
        cred = value
    elif input_type == 'name':
        result, message = handle_name_search(value, student_names)
        if isinstance(result, list):  # Multiple matches
            return message  # Return formatted list of matches
        if not result:
            return message  # Return error message
        cred = result
    else:
        return "❌ Invalid G0-number format. Should be like G02199"

    credentials = {
        "user_email": f"{cred}@apollo.lk",
        "password": cred
    }
    check_website(BASE_URL)
    subjects, sports, name = extract_marks(scrape_student_data(credentials))
    return format_single_user_output(name, subjects, sports)

def handle_first_input(command, student_names):
    """Handle first user input for comparison mode"""
    global first_user_data
    input_type, value = check_input(command)
    if input_type == 'g0':
        cred = value
    elif input_type == 'name':
        cred = handle_name_search(value, student_names)
        if not cred:
            return "❌ No matching names found or invalid selection"
    else:
        return "❌ Invalid G0-number format. Should be like G02199"

    credentials = {
        "user_email": f"{cred}@apollo.lk",
        "password": cred
    }
    check_website(BASE_URL)
    first_user_data = scrape_student_data(credentials)
    return ""

def handle_second_input(command, student_names):
    """Handle second user input and compare"""
    global first_user_data
    input_type, value = check_input(command)
    if input_type == 'g0':
        cred = value
    elif input_type == 'name':
        cred = handle_name_search(value, student_names)
        if not cred:
            return "❌ No matching names found or invalid selection"
    else:
        return "❌ Invalid G0-number format. Should be like G02199"

    credentials = {
        "user_email": f"{cred}@apollo.lk",
        "password": cred
    }
    #check_website(BASE_URL)
    second_user_data = scrape_student_data(credentials)
    
    subjects1, sports1, name1 = extract_marks(first_user_data)
    subjects2, sports2, name2 = extract_marks(second_user_data)
    
    return format_comparison_output(subjects1, sports1, subjects2, sports2, name1, name2)

def format_single_user_output(name, subjects, sports):
    """Format output for single user mode"""
    output = []
    output.append(f"\n👤 Student Name: {name}")
    
    output.append("\n📚 Subject Marks:")
    for subject, details in subjects.items():
        output.append(f"{subject}: {details['mark']} - {details['remark']} (Teacher: {details['teacher']})")
    
    output.append("\n🏆 Sports Marks:")
    for sport, details in sports.items():
        output.append(f"{sport}: {details['mark']} ({details['activity_type']}, {details['participation']})")
    
    return "\n".join(output)

def format_comparison_output(subjects1, sports1, subjects2, sports2, name1, name2):
    """Format output for comparison mode"""
    output = []
    output.append(f"\n📊 Comparing {name1} vs {name2}:")
    
    # Compare subject marks
    output.append("\n📚 Subject Marks Comparison:")
    for subject in subjects1.keys():
        if subject in subjects2:
            mark1 = int(subjects1[subject]['mark'])
            mark2 = int(subjects2[subject]['mark'])
            if mark1 > mark2:
                try:
                    diff = ((mark1 - mark2) / mark2) * 100
                    output.append(f"Difference in {subject}: {mark1} vs {mark2} ({name1.split()[0]} performed better by {diff:.1f}%)🔥")
                except ZeroDivisionError:
                    output.append(f"Difference in {subject}: {mark1} vs {mark2} ({name1.split()[0]} performed better by ∞)🔥")
            elif mark1 < mark2:
                try:
                    diff = ((mark2 - mark1) / mark1) * 100
                    output.append(f"Difference in {subject}: {mark1} vs {mark2} ({name2.split()[0]} performed better by {diff:.1f}%)💀")
                except ZeroDivisionError:
                    output.append(f"Difference in {subject}: {mark1} vs {mark2} ({name2.split()[0]} performed better by ∞)💀")
            else:
                output.append(f"No difference in {subject} performance (Mark: {mark1})⚖️")
        else:
            output.append(f"{subject} unique to {name1.split()[0]} with mark: {subjects1[subject]['mark']}📌")

    for subject in subjects2.keys():
        if subject not in subjects1:
            output.append(f"{subject} unique to {name2.split()[0]} with mark: {subjects2[subject]['mark']}📌")

    # Compare sports marks
    output.append("\n🏆 Sports Marks Comparison:")
    for sport in sports1.keys():
        if sport in sports2:
            mark1 = int(sports1[sport]['mark'])
            mark2 = int(sports2[sport]['mark'])
            if mark1 > mark2:
                try:
                    diff = ((mark1 - mark2) / mark2) * 100
                    output.append(f"Difference in {sport}: {mark1} vs {mark2} ({name1.split()[0]} performed better by {diff:.1f}%)🔥")
                except ZeroDivisionError:
                    output.append(f"Difference in {sport}: {mark1} vs {mark2} ({name1.split()[0]} performed better by ∞)🔥")
            elif mark1 < mark2:
                try:
                    diff = ((mark2 - mark1) / mark1) * 100
                    output.append(f"Difference in {sport}: {mark1} vs {mark2} ({name2.split()[0]} performed better by {diff:.1f}%)💀")
                except ZeroDivisionError:
                    output.append(f"Difference in {sport}: {mark1} vs {mark2} ({name2.split()[0]} performed better by ∞)💀")
            else:
                output.append(f"No difference in {sport} performance (Mark: {mark1})⚖️")
        else:
            output.append(f"{sport} unique to {name1.split()[0]} with mark: {sports1[sport]['mark']}📌")

    for sport in sports2.keys():
        if sport not in sports1:
            output.append(f"{sport} unique to {name2.split()[0]} with mark: {sports2[sport]['mark']}📌")

    return "\n".join(output)

def run_option_0():
    """Run single user stats mode"""
    student_names = load_student_names()
    cred = get_user_input("Enter G0-number or name (e.g., G02199 or Name): ", student_names)
    
    credentials = {
        "user_email": f"{cred}@apollo.lk",
        "password": cred
    }
    
    check_website(BASE_URL)
    subjects, sports, name = extract_marks(scrape_student_data(credentials))
    
    if name:
        display_single_user_stats(name, subjects, sports)
    else:
        print("❌ No data found for the user.")

def run_option_1():
    """Run comparison mode"""
    student_names = load_student_names()
    
    cred1 = get_user_input("\nEnter first G0-number or name: ", student_names)
    credentials1 = {
        "user_email": f"{cred1}@apollo.lk",
        "password": cred1
    }
    
    cred2 = get_user_input("\nEnter second G0-number or name: ", student_names)
    credentials2 = {
        "user_email": f"{cred2}@apollo.lk",
        "password": cred2
    }
    
    check_website(BASE_URL)
    
    subjects1, sports1, name1 = extract_marks(scrape_student_data(credentials1))
    subjects2, sports2, name2 = extract_marks(scrape_student_data(credentials2))
    
    if name1 and name2:
        compare(subjects1, sports1, subjects2, sports2, name1, name2)
    else:
        print("❌ Failed to get data for one or both users.")

def main():
    """Main program flow"""
    print("[0] Look at Me, I'm Awesome! (Your stats)")
    print("[1] Who's the Real MVP? (Comparison)")
    print("[2] Hasta La Vista, Baby (Exit)\n")
    
    choice = input("Enter your choice: ")
    print()
    
    if choice == "0":
        run_option_0()
    elif choice == "1":
        run_option_1()
    elif choice == "2":
        print("Adios, Amigos! 👋")
    else:
        print("Invalid choice!")

if __name__ == "__main__":
    main()
