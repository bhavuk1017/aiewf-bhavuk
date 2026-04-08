import re
import os

def append_new_scenarios(txt_path, turns_path):
    with open(txt_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Remove all lines matching "Tab X"
    content_cleaned = re.sub(r'(?m)^Tab \d+\s*\n', '', content)
    
    # Extract all scenario variable names
    scenario_names = re.findall(r'(?m)^(scenario_\w+) = \[', content_cleaned)

    if not scenario_names:
        print("No scenarios found to append.")
        return

    # Read target file
    with open(turns_path, "r", encoding="utf-8") as f:
        turns_content = f.read()

    # split the file just before "turns = ("
    split_marker = "turns = ("
    if split_marker not in turns_content:
        print(f"Could not find '{split_marker}' in {turns_path}")
        return

    parts = turns_content.split(split_marker)
    top_part = parts[0]
    bottom_part = split_marker + parts[1]

    # Check which scenarios are already in top_part to avoid duplicates
    new_code = ""
    added_names = []
    
    # We will split content_cleaned into individual blocks
    # One simple way is to use regex to capture each scenario assignment
    blocks = re.split(r'(?m)^(?=scenario_\w+ = \[)', content_cleaned)
    for block in blocks:
        block = block.strip()
        if not block: continue
        
        name_match = re.match(r'^(scenario_\w+) = \[', block)
        if name_match:
            s_name = name_match.group(1)
            if s_name not in top_part:
                new_code += "\n# =============================================================================\n"
                new_code += f"# {s_name}\n"
                new_code += "# =============================================================================\n\n"
                new_code += block + "\n\n"
                added_names.append(s_name)

    if not added_names:
        print("All scenarios already exist in turns.py.")
        return

    # Now we need to update the bottom_part adding `# + scenario_xxx` lines
    # bottom_part looks like:
    # turns = (
    #     # scenario_1_payment_done
    #      scenario_2_promise_to_pay
    #     # + scenario_3_settlement
    #     # + scenario_4_callback
    # )
    
    # Insert new names before the closing parenthesis
    closing_paren_idx = bottom_part.rfind(")")
    if closing_paren_idx != -1:
        insert_text = ""
        for name in added_names:
            insert_text += f"    # + {name}\n"
        
        bottom_part = bottom_part[:closing_paren_idx] + insert_text + bottom_part[closing_paren_idx:]

    final_content = top_part + new_code + bottom_part

    with open(turns_path, "w", encoding="utf-8") as f:
        f.write(final_content)
    
    print(f"Successfully appended {len(added_names)} scenarios to turns.py")
    for name in added_names:
        print(f" - {name}")


if __name__ == "__main__":
    txt_path = "/tmp/test_scenarios.txt"
    turns_path = "benchmarks/vapi_collections/turns.py"
    append_new_scenarios(txt_path, turns_path)
