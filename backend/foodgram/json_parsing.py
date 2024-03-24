import json

with open('data/ingredients.json', 'r') as file:
    data = json.load(file)

pk = 1
newdata=[]
for dict in data:
    newdata.append({"model": "api.ingredient",
                    "pk": pk,
                    "fields": dict})
    pk += 1

with open('backend/newdata.json', 'w') as file:
    json.dump(newdata, file,  ensure_ascii=False)