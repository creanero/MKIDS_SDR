# coding=utf-8

from PyQt4 import QtGui
import PyQt4.QtCore as QtC

class SIPrefixSpinbox(QtGui.QDoubleSpinBox):
    '''

    '''
    # Initial start from mguijarr via StackOverflow
    def __init__(self, *args):
        QtGui.QSpinBox.__init__(self, *args)
        #
        self.regex_string='(([+-]?\d+)[.]?(\d+)?[e]?[+-]?(\d+)?\s?([YZEPTGMkhdcmunpfazy])?)'
        self.rx = QtC.QRegExp(self.regex_string)
        self.validator = QtGui.QRegExpValidator(self.rx, self)

    def validate(self, text, pos):
        # this decides if the entered value should be accepted
        return self.validator.validate(text, pos)

    def textFromValue(self, value):
        si_value,si_prefix=SI_prefix_calculator(value)
        outstring = str(si_value)+si_prefix
        return outstring
    def valueFromText(self, p_str):
        str_no_suffix = self.cleanText()
        return SI_to_float(str_no_suffix)

    def setSuffix(self, p_str):
        super(SIPrefixSpinbox, self).setSuffix(p_str)
        self.regex_string=self.regex_string+'('+str(p_str)+')?'
        self.rx = QtC.QRegExp(self.regex_string)
        self.validator = QtGui.QRegExpValidator(self.rx, self)


def SI_to_float(in_string):
    si_value=in_string[:-1]
    si_prefix=in_string[-1]
    if si_prefix== 'Y':
        value=float(si_value)*1e24
    elif si_prefix== 'Z':
        value=float(si_value)*1e21
    elif si_prefix== 'E':
        value=float(si_value)*1e18
    elif si_prefix== 'P':
        value=float(si_value)*1e15
    elif si_prefix== 'T':
        value=float(si_value)*1e12
    elif si_prefix== 'G':
        value=float(si_value)*1e9
    elif si_prefix== 'M':
        value=float(si_value)*1e6
    elif si_prefix== 'k':
        value=float(si_value)*1e3
    elif si_prefix== 'h':
        value=float(si_value)*1e2
    elif si_prefix== 'da':
        value=float(si_value)*1e1
    elif si_prefix== 'd':
        value=float(si_value)*1e-1
    elif si_prefix== 'c':
        value=float(si_value)*1e-2
    elif si_prefix== 'm':
        value=float(si_value)*1e-3
    elif si_prefix== 'u':
        value=float(si_value)*1e-6
    elif si_prefix== 'μ':
        value=float(si_value)*1e-6
    elif si_prefix== 'n':
        value=float(si_value)*1e-9
    elif si_prefix== 'p':
        value=float(si_value)*1e-12
    elif si_prefix== 'f':
        value=float(si_value)*1e-15
    elif si_prefix== 'a':
        value=float(si_value)*1e-18
    elif si_prefix== 'z':
        value=float(si_value)*1e-21
    elif si_prefix== 'y':
        value=float(si_value)*1e-24
    else:
        value = float(in_string)
    return value

def SI_prefix_calculator(value):
    si_value=value
    si_prefix=''
    if value >= 1e24:
        si_value=value/1e24
        si_prefix= 'Y'
    elif value > 1e21:
        si_value=value/1e21
        si_prefix= 'Z'
    elif value >= 1e18:
        si_value=value/1e18
        si_prefix= 'E'
    elif value >= 1e15:
        si_value=value/1e15
        si_prefix= 'P'
    elif value >= 1e12:
        si_value=value/1e12
        si_prefix= 'T'
    elif value >= 1e9:
        si_value=value/1e9
        si_prefix= 'G'
    elif value >= 1e6:
        si_value=value/1e6
        si_prefix= 'M'
    elif value >= 1e3:
        si_value=value/1e3
        si_prefix= 'k'
    elif value >= 1:
        si_value=value/1
        si_prefix= ''
    elif value >= 1e-3:
        si_value=value/1e-3
        si_prefix= 'm'
    elif value >= 1e-6:
        si_value=value/1e-6
        si_prefix= 'μ'
    elif value >= 1e-9:
        si_value=value/1e-9
        si_prefix= 'n'
    elif value >= 1e-12:
        si_value=value/1e-12
        si_prefix= 'p'
    elif value >= 1e-15:
        si_value=value/1e-15
        si_prefix= 'f'
    elif value >= 1e-18:
        si_value=value/1e-18
        si_prefix= 'a'
    elif value >= 1e-21:
        si_value=value/1e-21
        si_prefix= 'z'
    elif value >= 1e-24:
        si_value=value/1e-24
        si_prefix= 'y'
    return si_value,si_prefix

