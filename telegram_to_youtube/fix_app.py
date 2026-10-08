with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip = False
for line in lines:
    if 'current_date = datetime.strptime' in line: continue
    if 'current_slot = start_slot' in line: continue
    
    if 'current_meta = {' in line: skip = True
    if 'current_time_str = times' in line: skip = True
    if 'current_slot += 1' in line: skip = True
    if 'if current_slot > 2:' in line: skip = True
    if 'tags = [word[1:]' in line: skip = True
    
    if skip and 'if profile_path:' in line:
        skip = False
        new_lines.append('                tags = [word[1:] for word in text.split() if word.startswith(\"#\")]\n')
        new_lines.append('                meta = { "title": title, "description": description, "tags": tags }\n')
        new_lines.append('                import json\n')
        new_lines.append('                with open(meta_path, "w", encoding="utf-8") as f:\n')
        new_lines.append('                    json.dump(meta, f, ensure_ascii=False, indent=4)\n')
        new_lines.append('                log("?? ??????? ????? ???????")\n')
    
    if not skip:
        new_lines.append(line)

with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
