# coding=utf-8
import warnings
from PyQt4 import QtGui
import PyQt4.QtCore as QtC

class SIPrefixSpinbox(QtGui.QDoubleSpinBox):
    '''

    '''
    # Initial start from mguijarr via StackOverflow
    def __init__(self, *args):
        QtGui.QSpinBox.__init__(self, *args)
        # complex regex string to recognise any possible number and the SI prefixes (including da as a separate case)
        self.regex_string='(([+-]?\d+)[.]?(\d+)?[e]?[+-]?(\d+)?\s?([YZEPTGMkhdcmunpfazy]|da)?)'
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
    '''
    This function takes a string with an SI prefix at the end of it and returns the value of the quantity in the base
    unit. For example, if given the string 20c it will return 0.2.  This is designed for use with the SIPrefixSpinBox
    class which extends the PyQT4 QDoubleSpinBox class, which can strip the base unit (e.g. Hz) from the value string
    before passing to this function.  If this is used elsewhere, then you need to handle that functionality yourself
    '''

    # parses the input string until it's possible to convert the leading characters into a float
    i = 0

    # sets default values to be returned if the next step fails.
    si_value = 0.0
    si_prefix = ''

    while i < len(in_string):
        try:
            # extracts the leading characters and converts them to a float
            si_value=float(in_string[:len(in_string)-i])
            # extracts the trailing characters for evaluation as an SI prefix
            si_prefix=in_string[len(in_string)-i:]
            # breaks the loop if it gets this far (expected failure on the float conversion)
            i=len(in_string)

        except ValueError:
            # increments the loop to split the input string one more character from the end.
            i=i+1

    # iterates over the SI prefixes
    if si_prefix== 'Y': # Yotta = 1e24
        value=si_value*1e24
    elif si_prefix== 'Z': # Zetta = 1e21
        value=si_value*1e21
    elif si_prefix== 'E': # Exa = 1e18
        value=si_value*1e18
    elif si_prefix== 'P': # Peta = 1e15
        value=si_value*1e15
    elif si_prefix== 'T': # Tera = 1e12
        value=si_value*1e12
    elif si_prefix== 'G': # Giga = 1e9
        value=si_value*1e9
    elif si_prefix== 'M': # Mega = 1e6
        value=si_value*1e6
    elif si_prefix== 'k': # Kilo = 1e3
        value=si_value*1e3
    elif si_prefix== 'h': # Hecto = 1e2
        value=si_value*1e2
    elif si_prefix== 'da': # Deca = 1e1
        value=si_value*1e1
    elif si_prefix== 'd': # deci = 1e-1
        value=si_value*1e-1
    elif si_prefix== 'c': # centi = 1e-2
        value=si_value*1e-2
    elif si_prefix== 'm': # milli = 1e-3
        value=si_value*1e-3
    elif si_prefix== 'u': # micro (ascii-limited) = 1e-6
        value=si_value*1e-6
    elif si_prefix== 'mc': # micro (ascii-limited) = 1e-6
        value=si_value*1e-6
    elif si_prefix== 'μ': # micro = 1e-6
        value=si_value*1e-6
    elif si_prefix== 'n': # nano = 1e-9
        value=si_value*1e-9
    elif si_prefix== 'p': # pico = 1e-12
        value=si_value*1e-12
    elif si_prefix== 'f': # femto = 1e-15
        value=si_value*1e-15
    elif si_prefix== 'a': # atto = 1e-18
        value=si_value*1e-18
    elif si_prefix== 'z': # zepto = 1e-21
        value=si_value*1e-21
    elif si_prefix== 'y': # yocto = 1e-24
        value=si_value*1e-24
    else: # no or unrecognised prefix
        value = si_value
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

