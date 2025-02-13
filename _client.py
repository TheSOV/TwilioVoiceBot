import requests
import json
import time
import pandas
import os
import dotenv
import phonenumbers
from colorama import init, Fore, Style
import shutil
from collections import ChainMap
from info_extraction import InfoExtractionAgent

# Initialize colorama
init()

info_agent = InfoExtractionAgent()

dotenv.load_dotenv()
PORT = int(os.getenv('PORT', 6060))
BOT_URL = f"http://localhost:{PORT}"

numbers_to_call_folder = "numbers_to_call"
call_results_folder = "call_results"

def get_numbers_to_call():
    available_files = []
    for file in os.listdir(numbers_to_call_folder):
        if file.endswith(".xlsx") or file.endswith(".xls") or file.endswith(".csv"):
            available_files.append(file)

    selected_file = None
    while selected_file is None:
        if len(available_files) == 0:
            input(f"{Fore.RED}No hay ficheros disponibles.{Style.RESET_ALL} Presiona enter para salir.")
            exit()
            
        if len(available_files) > 0:
            
            print()
            print(f"{Fore.CYAN}Selecciona un fichero:{Style.RESET_ALL}")
            for i, file in enumerate(available_files):
                print(f"{Fore.GREEN}{i+1}. {file}{Style.RESET_ALL}")

            print()
            selected_file_index = input(f"{Fore.YELLOW}Selecciona un fichero por su número: {Style.RESET_ALL}")
            
            if selected_file_index.isdigit() and 1 <= int(selected_file_index) <= len(available_files):
                selected_file = available_files[int(selected_file_index) - 1]
            else:
                print(f"{Fore.RED}Selecciona un número de fichero válido.{Style.RESET_ALL}")
                continue

    numbers_to_call = []

    if selected_file.endswith(".xlsx") or selected_file.endswith(".xls"):
        df = pandas.read_excel(os.path.join(numbers_to_call_folder, selected_file), header=None)
        # Select only the first column and convert to strings
        numbers_to_call = df.iloc[:, 0].astype(str).tolist()
    elif selected_file.endswith(".csv"):
        df = pandas.read_csv(os.path.join(numbers_to_call_folder, selected_file), header=None)
        # Select only the first column and convert to strings
        numbers_to_call = df.iloc[:, 0].astype(str).tolist()
    else:
        raise Exception(f"El formato de fichero no es válido.")
    
    return numbers_to_call

def validate_number(number):
    number = str(number)
    try:
        parsed_number = phonenumbers.parse(number, "ES")
        formatted_number = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
        if len(formatted_number) != 12:
            return None, f"El formato del número no es correcto: {number}"
        return formatted_number, None
    except phonenumbers.NumberParseException:
        return None, f"El número no es válido: {number}."
    

if __name__ == "__main__":
    numbers_to_call = get_numbers_to_call()
    validated_numbers = []

    for number in numbers_to_call:
        formatted_number, error = validate_number(number)
        if formatted_number:
            validated_numbers.append(formatted_number)
        else:
            print(error)

    print()    
    print(f"{Fore.GREEN}Números a llamar:{Style.RESET_ALL} {len(validated_numbers)}")

    results = []

    for number in validated_numbers:
        print(f"{Fore.CYAN}LLamando a: {number}{Style.RESET_ALL}")
        response = requests.post(f"{BOT_URL}/make_call", json={"phone_number": number})

        save_path = os.path.join(call_results_folder, f"{number}")
        os.makedirs(save_path, exist_ok=True)
        
        # Copy the recording to the new directory
        recordings_combined_folder = os.path.join(os.path.dirname(__file__))
        recording_source = os.path.join(recordings_combined_folder, response.json()["audio_file_name"])
        recording_destination = os.path.join(save_path, f"combined_audio_{number}.wav")
        shutil.copy2(recording_source, recording_destination)

        print(f"{Fore.CYAN}Transcribiendo y recopilando información...{Style.RESET_ALL}")
        information, conversation = info_agent.extract_info(recording_destination)

        print(f"{Fore.GREEN}Información extraida:{Style.RESET_ALL}")
        data = {}

        print("Information:")
        for key, value in information.model_dump()["parsed"].items():
            data[key] = value
            print(f"{key}: {value}")

        print("\nResponse:")
        for key, value in response.json().items():
            data[key] = value
            print(f"{key}: {value}")
        
        print("\nConversation:")
        for turn in conversation:
            print(f"{turn['speaker']}: {turn['text']}")
        
        data["conversation"] = "\n".join([f"{turn['speaker']}: {turn['text']}" for turn in conversation])
     
        results.append(data)

        df = pandas.DataFrame(results)
        df.to_excel(os.path.join("call_results", f"call_results_{time.strftime('%Y-%m-%d_%H-%M-%S')}.xlsx"), index=False)
