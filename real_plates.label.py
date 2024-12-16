import os

# names: ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'be', 'dal', 'ein', 'ghaf', 'h',  'jim', 'lam', 'mim', 'noon', 'sad', 'sin', 'ta', 'te', 'waw', 'ye']
# names: ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11',  '12' ,  '13',  '14', '15',  '16',  '17',  '18',   '19',  '20',  '21', '22', '23',  '24']
# names: ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'b',  'd',   'e' ,   'q',   '#',  'j',   'l',   'm',   'n',    '@',   's',   '!',  't',  'v',   'y']

symbols = {
    '0':'0',
    '1':'1',
    '2':'2',
    '3':'3',
    '4':'4',
    '5':'5',
    '6':'6',
    '7':'7',
    '8':'8',
    '9':'9',
    #####################
    '12':'e', # EIN
    '14':'#',
    '20':'s',
    '19':'@',
    '21':'!',
    '10':'b',
    '18':'n',
    '22':'t',
    # 'H':'h',
    '11':'d',
    '13':'q',
    '15':'j',
    '23':'v',
    '17':'m',
    '24':'y',
    '16':'l',
}

def get_labels(label_file_path):
    labels = []
    with open(label_file_path, 'r') as file:
        chars = []
        for line in file:
            # Assuming each line contains a label in the format: class_name x y w h
            parts = line.strip().split()
            # if len(parts) == 6:  # Check if the line has the expected number of parts
            temp = list(map(float, parts))
            chars.append(temp)
        chars.sort(key=lambda x: x[1])    
        # labels.append(parts[0])  # Add the class name to the list
        labels = [str(int(c[0])) for c in chars]
    return labels

base_path = './input/all-plates/'
files = os.listdir(base_path)
counter = 0
for file in files:
    if file.endswith(".jpg"):
        
        label_file_path = file.replace('.jpg', '.txt')
        try:
            labels = get_labels(base_path+label_file_path)
        except:
            print("Removed Image")
            os.remove(base_path+file)
            continue
        if len(labels) != 8:
            os.remove(base_path+file)
            os.remove(base_path+label_file_path)
            print("Removed Image and labels")
            continue
        labels = [l.replace(l,symbols[l]) for l in labels]
        new_label = ''.join(labels)
        counter +=1
        os.rename(base_path+file , base_path+str(counter)+'_'+new_label+'.jpg')
        # print(labels)
        
        


      







        
        
        
        
        
        
        
        