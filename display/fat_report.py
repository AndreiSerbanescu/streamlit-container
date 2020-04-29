import streamlit as st
from functools import reduce
import operator

class FatReportDisplayer:

    def __init__(self, original_array, lung_seg_array, fat_report_csv, fat_interval=None):

        self.original_array = original_array
        self.lung_seg_array = lung_seg_array
        self.fat_report = self.__convert_report_to_cm3(fat_report_csv)
        self.fat_interval = fat_interval

        self.paper_citation = "**Fat Measurement by:** Summers RM, Liu J, Sussman DL, Dwyer AJ, Rehani B, " \
                              "Pickhardt PJ, Choi JR, Yao J. Association " \
                              "Between Visceral Adiposity and Colorectal Polyps on CT Colonography. AJR 199:48–57 (2012)." \
                              "Ryckman EM, Summers RM, Liu J, Del Rio AM, Pickhardt PJ. Visceral fat quantification in asymptomatic " \
                              "adults using abdominal CT: is it predictive of future cardiac events? Abdom Imaging 40:222–225 (2015)." \
                              "Liu J, Pattanaik S, Yao J, Dwyer AJ, Pickhardt PJ, Choi JR, Summers RM. Associations among Pericolonic Fat, Visceral Fat, " \
                              "and Colorectal Polyps on CT Colonography. Obesity 23:470-476 (2015)." \
                              "Lee SJ, Liu J, Yao J, Kanarek A, Summers RM, Pickhardt PJ. Fully Automated Segmentation" \
                              " and Quantification of Visceral and Subcutaneous Fat at Abdominal CT: Application to a " \
                              "  longitudinal adult screening cohort. Br J Radiol 91(1089):20170968 (2018)"

        self.sat_vols = [elem['satVol'] for elem in self.fat_report]
        self.vat_vols = [elem['vatVol'] for elem in self.fat_report]

    def display(self):

        st.markdown(self.paper_citation)
        st.markdown('**Fat Report**')

        fat_report_len = len(self.fat_report)

        assert len(self.vat_vols) == len(self.sat_vols) == len(self.fat_report)

        st.markdown("**Total fat tissue information**")
        self.__display_agg_info(0, fat_report_len)

        st.markdown("**Lower half tissue information**")
        self.__display_agg_info(fat_report_len // 2, fat_report_len)

        st.markdown("**Lower third tissue information**")
        self.__display_agg_info(fat_report_len * 2 // 3, fat_report_len)

        if self.fat_interval is not None:
            top, bottom = self.fat_interval

            from_slice = int(top * fat_report_len / 100)
            to_slice = int(bottom * fat_report_len / 100)

            st.markdown(f"**Custom from slice {from_slice} to slice {to_slice}**")
            self.__display_agg_info(from_slice, to_slice)


        self.__display_confidence_interval()

    def get_converted_report(self):
        return self.fat_report

    def __display_agg_info(self, from_slice, to_slice):
        # from_slice inclusive
        # to_slice exclusive

        partial_sats = self.sat_vols[from_slice:to_slice]
        partial_vats = self.vat_vols[from_slice:to_slice]

        sat_tissue_cm3 = reduce(operator.add, partial_sats)
        vat_tissue_cm3 = reduce(operator.add, partial_vats)

        st.text(f"visceral to subcutaneous ratio {vat_tissue_cm3 / sat_tissue_cm3}")
        st.text(f"visceral volume: {vat_tissue_cm3:.2f} cm3")
        st.text(f"subcutaneous volume: {sat_tissue_cm3:.2f} cm3")

    def __display_confidence_interval(self):
        #TODO implement
        pass

    def __convert_report_to_cm3(self, fat_report):

        last_row = fat_report[-1]
        fat_report = fat_report[:len(fat_report) - 1]

        visceral_tissue = 0
        subcutaneous_tissue = 0
        for row in fat_report:
            visceral_tissue += float(row['vatVol'])
            subcutaneous_tissue += float(row['satVol'])

        total_in_cm3 = float(last_row["tatVol"])
        total = visceral_tissue + subcutaneous_tissue

        ratio = total_in_cm3 / total

        fat_report_cm3 = []
        for row in fat_report:
            visceral_tissue = float(row['vatVol'])
            subcutaneous_tissue = float(row['satVol'])

            visc_tissue_cm3 = ratio * visceral_tissue
            subcut_tissue_cm3 = ratio * subcutaneous_tissue

            row_dict_cm3 = {
                'vatVol': visc_tissue_cm3,
                'satVol': subcut_tissue_cm3
            }

            fat_report_cm3.append(row_dict_cm3)

        return fat_report_cm3

# def __display_partial_volume(volume, from_slice, to_slice):
#
#     volume_array = sitk.GetArrayFromImage(volume)
#
#     cm = plt.get_cmap('gray')
#     cm_hot = plt.get_cmap('inferno')  # copper
#     zd, yd, xd = volume_array.shape
#
#     im = volume_array[from_slice:to_slice, yd // 2, :]
#     im = np.uint8(cm(im) * 255)
#
#     im = Image.fromarray(im).convert('RGB')
#     im = im.resize((150, 150))
#     # im = np.uint8(cm_hot(segmentation_array[i, :, :].astype(float) / num_labels) * 255)
#     # im = Image.fromarray(im).convert('RGB')
#     # imgs.append(im.resize((150, 150)))
#     st.image(im)