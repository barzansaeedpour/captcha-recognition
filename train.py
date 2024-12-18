import os
import glob
import torch
import numpy as np

import albumentations
from sklearn import preprocessing
from sklearn import model_selection
from sklearn import metrics

import config
import dataset
import engine
from model import CaptchaModel


from torch import nn


def remove_duplicates(x):
    if len(x) < 2:
        return x
    fin = ""
    for j in x:
        if fin == "":
            fin = j
        else:
            if j == fin[-1]:
                continue
            else:
                fin = fin + j
    return fin


def decode_predictions(preds, encoder):
    preds = preds.permute(1, 0, 2)
    preds = torch.softmax(preds, 2)
    preds = torch.argmax(preds, 2)
    preds = preds.detach().cpu().numpy()
    cap_preds = []
    for j in range(preds.shape[0]):
        temp = []
        for k in preds[j, :]:
            k = k - 1
            if k == -1:
                temp.append("§")
            else:
                p = encoder.inverse_transform([k])[0]
                temp.append(p)
        tp = "".join(temp).replace("§", "")
        # tp = "".join(temp)
        cap_preds.append(remove_duplicates(tp))
    return cap_preds


def run_training():
    # image_files = glob.glob(os.path.join(config.DATA_DIR, "*.png"))
    image_files = glob.glob(os.path.join(config.DATA_DIR, "*.jpg"))
    image_files = [f.replace('\\','/') for f in image_files]
    # targets_orig = [x.split("/")[-1][:-4] for x in image_files]
    targets_orig = [x.split("/")[-1][:-4].split('_')[1] for x in image_files]
    for t in targets_orig:
        if not len(t)==8:
            print('ok')
    targets = [[c for c in x] for x in targets_orig]
    targets_flat = [c for clist in targets for c in clist]

    lbl_enc = preprocessing.LabelEncoder()
    lbl_enc.fit(targets_flat)
    targets_enc = [lbl_enc.transform(x) for x in targets]
    targets_enc = np.array(targets_enc)
    targets_enc = targets_enc + 1

    (
        train_imgs,
        test_imgs,
        train_targets,
        test_targets,
        _,
        test_targets_orig,
    ) = model_selection.train_test_split(
        image_files, targets_enc, targets_orig, test_size=0.1, random_state=42
    )

    train_dataset = dataset.ClassificationDataset(
        image_paths=train_imgs,
        targets=train_targets,
        resize=(config.IMAGE_HEIGHT, config.IMAGE_WIDTH),
    )
    train_loader = torch.utils.data.DataLoader(
        train_dataset,
        batch_size=config.BATCH_SIZE,
        num_workers=config.NUM_WORKERS,
        shuffle=True,
    )
    test_dataset = dataset.ClassificationDataset(
        image_paths=test_imgs,
        targets=test_targets,
        resize=(config.IMAGE_HEIGHT, config.IMAGE_WIDTH),
    )
    test_loader = torch.utils.data.DataLoader(
        test_dataset,
        batch_size=config.BATCH_SIZE,
        num_workers=config.NUM_WORKERS,
        shuffle=False,
    )

    model = CaptchaModel(num_chars=len(lbl_enc.classes_))
    model.to(config.DEVICE)

    optimizer = torch.optim.Adam(model.parameters(), lr=3e-4)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, factor=0.8, patience=5, verbose=True
    )
    for epoch in range(config.EPOCHS):
        train_loss = engine.train_fn(model, train_loader, optimizer)
        valid_preds, test_loss = engine.eval_fn(model, test_loader)
        # valid_captcha_preds = []
        # for vp in valid_preds:
        #     current_preds = decode_predictions(vp, lbl_enc)
        #     valid_captcha_preds.extend(current_preds)
        # print(list(zip(test_targets_orig, valid_captcha_preds))[6:10])
        # print(f"Epoch={epoch}, Train Loss={train_loss}, Test Loss={test_loss}")
        valid_captcha_preds = []
        for vp in valid_preds:
            current_preds = decode_predictions(vp, lbl_enc)
            valid_captcha_preds.extend(current_preds)
        combined = list(zip(test_targets_orig, valid_captcha_preds))
        print(combined[:10])
        test_dup_rem = [remove_duplicates(c) for c in test_targets_orig]
        accuracy = metrics.accuracy_score(test_dup_rem, valid_captcha_preds)
        print(
            f"Epoch={epoch}, Train Loss={train_loss}, Test Loss={test_loss} Accuracy={accuracy}"
        )
        scheduler.step(test_loss)

        # Save the model if accuracy is 1 
        if accuracy >= 0.8: 
            save_path = os.path.join(config.MODEL_SAVE_DIR, f"model_epoch_{epoch}_accuracy_{accuracy:.4f}.pth") 
            torch.save(model.state_dict(), save_path) 
            print(f"Model saved at {save_path}")

def run_testing():
    # image_files = glob.glob(os.path.join(config.DATA_DIR, "*.png"))
    image_files = glob.glob(os.path.join(config.TEST_DATA_DIR, "*.jpg"))
    image_files = [f.replace('\\','/') for f in image_files]
    # targets_orig = [x.split("/")[-1][:-4] for x in image_files]
    targets_orig = [x.split("/")[-1][:-4].split('_')[1] for x in image_files]
    targets = [[c for c in x] for x in targets_orig]
    targets_flat = [c for clist in targets for c in clist]

    lbl_enc = preprocessing.LabelEncoder()
    lbl_enc.fit(targets_flat)
    targets_enc = [lbl_enc.transform(x) for x in targets]
    targets_enc = np.array(targets_enc)
    targets_enc = targets_enc + 1

    (
        train_imgs,
        test_imgs,
        train_targets,
        test_targets,
        _,
        test_targets_orig,
    ) = model_selection.train_test_split(
        image_files, targets_enc, targets_orig, test_size=0.96, random_state=42
    )

    # train_dataset = dataset.ClassificationDataset(
    #     image_paths=train_imgs,
    #     targets=train_targets,
    #     resize=(config.IMAGE_HEIGHT, config.IMAGE_WIDTH),
    # )
    # train_loader = torch.utils.data.DataLoader(
    #     train_dataset,
    #     batch_size=config.BATCH_SIZE,
    #     num_workers=config.NUM_WORKERS,
    #     shuffle=True,
    # )
    test_dataset = dataset.ClassificationDataset(
        image_paths=test_imgs,
        targets=test_targets,
        resize=(config.IMAGE_HEIGHT, config.IMAGE_WIDTH),
    )
    test_loader = torch.utils.data.DataLoader(
        test_dataset,
        batch_size=config.BATCH_SIZE,
        num_workers=config.NUM_WORKERS,
        shuffle=False,
    )

    # model = CaptchaModel(num_chars=10)
    # model.to(config.DEVICE)
    
    # Test a single image 
    
    model_path = "./model_epoch_110_accuracy_0.9853.pth" 
    # Load the trained model 
    model = CaptchaModel(num_chars=len(lbl_enc.classes_)) 
    model.load_state_dict(torch.load(model_path)) 
    model.to(config.DEVICE)
    

    optimizer = torch.optim.Adam(model.parameters(), lr=3e-4)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, factor=0.8, patience=5, verbose=True
    )
    # for epoch in range(config.EPOCHS):
    # train_loss = engine.train_fn(model, train_loader, optimizer)
    valid_preds, test_loss = engine.eval_fn(model, test_loader)
    # valid_captcha_preds = []
    # for vp in valid_preds:
    #     current_preds = decode_predictions(vp, lbl_enc)
    #     valid_captcha_preds.extend(current_preds)
    # print(list(zip(test_targets_orig, valid_captcha_preds))[6:10])
    # print(f"Epoch={epoch}, Train Loss={train_loss}, Test Loss={test_loss}")
    valid_captcha_preds = []
    for vp in valid_preds:
        current_preds = decode_predictions(vp, lbl_enc)
        valid_captcha_preds.extend(current_preds)
    combined = list(zip(test_targets_orig, valid_captcha_preds))
    print(combined[:10])
    test_dup_rem = [remove_duplicates(c) for c in test_targets_orig]
    accuracy = metrics.accuracy_score(test_dup_rem, valid_captcha_preds)
    print(
        f"Test Loss={test_loss} Accuracy={accuracy}"
    )
    scheduler.step(test_loss)


if __name__ == "__main__":
    # run_training()
    run_testing()
