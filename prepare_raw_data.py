import re
import json

with open("files/text.txt", "r") as file:
    topic_pattern = r"[VI]+\. (.*)"
    question_pattern = r"(\d+)\. В: (.*)"
    answer_pattern = r"О: (.*)"
    link_pattern = r"Ссылка: \[.*\]\((.+)\)"
    last_topic = None
    question = None
    last_topic_index = -1
    local_id = 0
    d = {"topics": []}
    for line in file.readlines():
        line = line.strip()
        if not line:
            continue
        topic = re.match(topic_pattern, line)
        if topic:
            # print(f"Topic: {topic[0]}")
            topic = topic[0]
            last_topic_index += 1
            local_id = 0
            d["topics"].append({"name": topic, "id": last_topic_index, "questions": []})
            continue
        question_pattern_match = re.findall(question_pattern, line)
        if question_pattern_match:
            # print(f"Question: {question_pattern_match[0]}")
            question = question_pattern_match[0][1]
            question_id = question_pattern_match[0][0]
            # print(f"Current question: {question}, id: {question_id}")
            continue
        answer_pattern_match = re.match(answer_pattern, line)
        if answer_pattern_match:
            # print(f"Answer: {answer_pattern_match[0]}")
            if question is None:
                raise ValueError("Answer without question")
            answer = answer_pattern_match[0]
            continue
        link_pattern_match = re.findall(link_pattern, line)
        if link_pattern_match:
            if answer is None:
                raise ValueError("Link without answer")
            que_ans = {
                "question": question,
                "answer": answer,
                "link": link_pattern_match[0],
                "id": int(question_id),
                "local_id": int(local_id)
            }
            local_id += 1
            d["topics"][last_topic_index]["questions"].append(que_ans)
            question, answer = None, None
            continue
        else:
            print(f"Unknown line: {line}")
            continue
    # print(f"Final data: {d}")
    file.close()

with open("files/data_2.json", "w", encoding="utf-8") as file:
    json.dump(d, file, ensure_ascii=False, indent=2)
    file.close()