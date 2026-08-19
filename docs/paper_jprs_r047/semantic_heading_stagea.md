# r047 Stage A status

The clean formal Stage A completed its required development and calibration stages. Four arms (AHC, WHOLE_CROP, CONCAT_ENDPOINT, HEADPOINT_REG) ran 30 epochs with four-rank DDP using the registered HRSC R50 backbone mapping. After the remotely visible model seal, T_cal-only calibration was performed for GT_BOX, R50 and LSKNet views. No common nominal coverage at or above 0.70 satisfied the frozen Bentkus-UCB risk bound of 0.15, so the stage terminates at `REJECT_AHC_OBB_VALID_TCAL_SAFETY_FAIL`. T_audit was not opened and no deployable/scientific-positive claim is made.
