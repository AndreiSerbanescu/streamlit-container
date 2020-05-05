import SimpleITK as sitk
from sklearn.metrics import f1_score, jaccard_score
import numpy as np

def dice_score(ground_np, pred_np):
    return f1_score(ground_np.ravel(), pred_np.ravel())

def intersection_over_union(ground_np, pred_np):
    return jaccard_score(ground_np.ravel(), pred_np.ravel())

def get_complete_set_of_dice_scores(seg_sitk, ground_left_sitk, ground_right_sitk):

    seg_np          = sitk.GetArrayFromImage(seg_sitk)
    ground_left_np  = sitk.GetArrayFromImage(ground_left_sitk)
    ground_right_np = sitk.GetArrayFromImage(ground_right_sitk)

    seg_left_np = np.where(seg_np == 1, 0, seg_np)
    seg_left_np = np.where(seg_left_np == 2, 1, seg_left_np)
    seg_right_np = np.where(seg_np == 2, 0, seg_np)
    ground_left_np = np.where(ground_left_np == 255, 1, ground_left_np)
    ground_right_np = np.where(ground_right_np == 255, 1, ground_right_np)


    left_dice_score = dice_score(ground_left_np, seg_left_np)
    right_dice_score = dice_score(ground_right_np, seg_right_np)

    both_lungs_ground = np.add(ground_left_np, ground_right_np)
    both_lungs_seg = np.where(seg_np == 2, 1, seg_np)

    both_lungs_dice_score = dice_score(both_lungs_seg, both_lungs_ground)

    return left_dice_score, right_dice_score, both_lungs_dice_score

def get_complete_set_of_iou_scores(seg_sitk, ground_left_sitk, ground_right_sitk):

    seg_np          = sitk.GetArrayFromImage(seg_sitk)
    ground_left_np  = sitk.GetArrayFromImage(ground_left_sitk)
    ground_right_np = sitk.GetArrayFromImage(ground_right_sitk)

    seg_left_np = np.where(seg_np == 1, 0, seg_np)
    seg_left_np = np.where(seg_left_np == 2, 1, seg_left_np)
    seg_right_np = np.where(seg_np == 2, 0, seg_np)
    ground_left_np = np.where(ground_left_np == 255, 1, ground_left_np)
    ground_right_np = np.where(ground_right_np == 255, 1, ground_right_np)

    left_iou_score = intersection_over_union(ground_left_np, seg_left_np)
    right_iou_score = intersection_over_union(ground_right_np, seg_right_np)

    both_lungs_ground = np.add(ground_left_np, ground_right_np)
    both_lungs_seg = np.where(seg_np == 2, 1, seg_np)

    both_lungs_iou_score = intersection_over_union(both_lungs_ground, both_lungs_seg)

    return left_iou_score, right_iou_score, both_lungs_iou_score

if __name__ == "__main__":
    from workers.nifti_reader import read_nifti_image
    import os

    base_dir = "/app/output/LCTSC-Test-S1-101/"
    seg = read_nifti_image(os.path.join(base_dir, "lungmask_nifti.nii.gz"))
    ground_left = read_nifti_image(os.path.join(base_dir, "ground_left.nii.gz"))
    ground_right = read_nifti_image(os.path.join(base_dir, "ground_right.nii.gz"))

    left_dice, right_dice, full_dice = get_complete_set_of_dice_scores(seg, ground_left, ground_right)

    print("left dice", left_dice)
    print("right dice", right_dice)
    print("both dice", full_dice)