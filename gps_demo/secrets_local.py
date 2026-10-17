"""Lectura local DPAPI; nunca devolver el secreto en registros ni HTTP."""
import ctypes
import json
import os
from ctypes import wintypes

from .pipeline import ROOT


def meta_settings(root=ROOT):
    data = json.loads((root / 'config/meta.local.json').read_text(encoding='utf-8-sig'))
    if os.name != 'nt':
        raise ValueError('El secreto DPAPI requiere la cuenta Windows que lo guardó')
    class Blob(ctypes.Structure):
        _fields_ = [('size', wintypes.DWORD), ('data', ctypes.POINTER(ctypes.c_byte))]
    encrypted = bytes.fromhex(data['token_protected'])
    buffer = (ctypes.c_byte * len(encrypted)).from_buffer_copy(encrypted)
    source = Blob(len(encrypted), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_byte)))
    target = Blob()
    crypt = ctypes.WinDLL('crypt32', use_last_error=True)
    crypt.CryptUnprotectData.argtypes = [ctypes.POINTER(Blob), ctypes.c_void_p, ctypes.c_void_p,
                                        ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(Blob)]
    crypt.CryptUnprotectData.restype = wintypes.BOOL
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    kernel.LocalFree.restype = ctypes.c_void_p
    if not crypt.CryptUnprotectData(ctypes.byref(source), None, None, None, None, 1, ctypes.byref(target)):
        raise ValueError('No se pudo descifrar el token con esta cuenta Windows')
    try:
        token = ctypes.string_at(target.data, target.size).decode('utf-16-le')
    finally:
        ctypes.memset(target.data, 0, target.size)
        kernel.LocalFree(ctypes.cast(target.data, ctypes.c_void_p))
    return token, data['phone_number_id'], data['graph_version']
