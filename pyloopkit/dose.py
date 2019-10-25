#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Aug 15 09:54:54 2019

@author: annaquinlan
"""
from enum import Enum


class DoseType(Enum):
    suspend = 0
    resume = 1
    basal = 2
    tempbasal = 3
    bolus = 4
    meal = 5  # meals are included for compatability with Loop tests

    @staticmethod
    def from_str(label):
        if label.lower() in ["suspend", "pumpsuspend"]:
            return DoseType.suspend
        elif label.lower() in ["resume", "pumpresume"]:
            return DoseType.resume
        elif label.lower() in ["basal", "basalprofilestart"]:
            return DoseType.basal
        elif label.lower() == "tempbasal":
            return DoseType.tempbasal
        elif label.lower() == "bolus":
            return DoseType.bolus
        elif label.lower() == "meal":
            return DoseType.meal
        else:
            raise NotImplementedError(label, "not recognized")
