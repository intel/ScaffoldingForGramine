# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2023 Intel Corporation
#                    Wojtek Porczyk <woju@invisiblethingslab.com>

import ctypes
import http.client
import multiprocessing
import os
import ssl
import types
import urllib.parse


class AttestationError(Exception):
    pass


def request(method, url, *, verify_cb, headers=types.MappingProxyType({}),
        data=None):
    url = urllib.parse.urlsplit(url)
    if url.scheme != 'https':
        raise ValueError(f'needs https:// URI, found {url.scheme}://')

    context = ssl._create_unverified_context() #pylint: disable=protected-access
    conn = http.client.HTTPSConnection(url.netloc, context=context)
    conn.connect()
    try:
        # NEVER SEND ANYTHING TO THE SERVER BEFORE THIS LINE
        verify_cb(conn.sock.getpeercert(binary_form=True))
    except AttestationError:
        conn.close()
        raise

    path = url.path
    if url.query:
        path += url.query
    headers = {
        'host': url.hostname,
        **headers,
    }

    conn.request(method, path, headers=headers, body=data)
    return conn.getresponse()


def ra_tls_setenv(var, value, default=None):
    if value in (None, False):
        if default is None:
            try:
                del os.environ[var]
            except KeyError:
                pass
        else:
            os.environ[var] = default
    elif value is True:
        os.environ[var] = '1'
    else:
        os.environ[var] = value

def _ra_tls_verify_callback_der(scheme, der, ret):
    # At the time of this writing (October 2023) ra_tls_ libraries output
    # diagnostic information to stdout.
    os.dup2(2, 1)

    lib = ctypes.cdll.LoadLibrary(f'libra_tls_verify_{scheme}.so')
    func = lib.ra_tls_verify_callback_der # TODO extended
    func.argtypes = ctypes.c_char_p, ctypes.c_size_t
    func.restype = ctypes.c_int
    ret.value = func(der, len(der))

def ra_tls_verify_callback_der(scheme, der):
    ret = multiprocessing.Value(ctypes.c_int)
    proc = multiprocessing.Process(target=_ra_tls_verify_callback_der, args=(scheme, der, ret))
    proc.start()
    proc.join()

    if ret.value < 0:
        raise AttestationError(ret)


VERIFY_CB = {}

def verify_dcap(cert, *,
    mrenclave=None, mrsigner=None, isv_prod_id=None, isv_svn=None,
    allow_debug_enclave_insecure=False, allow_outdated_tcb_insecure=False,
    allow_hw_config_needed=False, allow_sw_hardening_needed=False,
):
    if (mrenclave, mrsigner) == (None, None):
        raise TypeError('need at least one of: mrenclave, mrsigner')

    ra_tls_setenv('RA_TLS_MRENCLAVE', mrenclave, 'any')
    ra_tls_setenv('RA_TLS_MRSIGNER', mrsigner, 'any')
    ra_tls_setenv('RA_TLS_ISV_PROD_ID', isv_prod_id, 'any')
    ra_tls_setenv('RA_TLS_ISV_SVN', isv_svn, 'any')
    ra_tls_setenv('RA_TLS_ALLOW_DEBUG_ENCLAVE_INSECURE', allow_debug_enclave_insecure)
    ra_tls_setenv('RA_TLS_ALLOW_OUTDATED_TCB_INSECURE', allow_outdated_tcb_insecure)
    ra_tls_setenv('RA_TLS_ALLOW_HW_CONFIG_NEEDED', allow_hw_config_needed)
    ra_tls_setenv('RA_TLS_ALLOW_SW_HARDENING_NEEDED', allow_sw_hardening_needed)

    ra_tls_verify_callback_der('dcap', cert)

VERIFY_CB['dcap'] = verify_dcap


def verify_epid(cert, *,
    epid_api_key,
    mrenclave=None, mrsigner=None, isv_prod_id=None, isv_svn=None,
    allow_debug_enclave_insecure=False, allow_outdated_tcb_insecure=False,
    allow_hw_config_needed=False, allow_sw_hardening_needed=False,
    ias_report_url=None, ias_sigrl_url=None, ias_pub_key_pem=None,
):
    if (mrenclave, mrsigner) == (None, None):
        raise TypeError('need at least one of: mrenclave, mrsigner')

    ra_tls_setenv('RA_TLS_EPID_API_KEY', epid_api_key)
    ra_tls_setenv('RA_TLS_MRENCLAVE', mrenclave, 'any')
    ra_tls_setenv('RA_TLS_MRSIGNER', mrsigner, 'any')
    ra_tls_setenv('RA_TLS_ISV_PROD_ID', isv_prod_id, 'any')
    ra_tls_setenv('RA_TLS_ISV_SVN', isv_svn, 'any')
    ra_tls_setenv('RA_TLS_ALLOW_DEBUG_ENCLAVE_INSECURE', allow_debug_enclave_insecure)
    ra_tls_setenv('RA_TLS_ALLOW_OUTDATED_TCB_INSECURE', allow_outdated_tcb_insecure)
    ra_tls_setenv('RA_TLS_ALLOW_HW_CONFIG_NEEDED', allow_hw_config_needed)
    ra_tls_setenv('RA_TLS_ALLOW_SW_HARDENING_NEEDED', allow_sw_hardening_needed)
    ra_tls_setenv('RA_TLS_IAS_REPORT_URL', ias_report_url)
    ra_tls_setenv('RA_TLS_IAS_SIGRL_URL', ias_sigrl_url)
    ra_tls_setenv('RA_TLS_IAS_PUB_KEY_PEM', ias_pub_key_pem)

    ra_tls_verify_callback_der('epid', cert)

VERIFY_CB['epid'] = verify_epid


def verify_maa(cert, *,
    maa_provider_url,
    mrenclave=None, mrsigner=None, isv_prod_id=None, isv_svn=None,
    allow_debug_enclave_insecure=False, maa_provider_api_version=None,
):
    if (mrenclave, mrsigner) == (None, None):
        raise TypeError('need at least one of: mrenclave, mrsigner')

    ra_tls_setenv('RA_TLS_MAA_PROVIDER_URL', maa_provider_url)
    ra_tls_setenv('RA_TLS_MRENCLAVE', mrenclave, 'any')
    ra_tls_setenv('RA_TLS_MRSIGNER', mrsigner, 'any')
    ra_tls_setenv('RA_TLS_ISV_PROD_ID', isv_prod_id, 'any')
    ra_tls_setenv('RA_TLS_ISV_SVN', isv_svn, 'any')
    ra_tls_setenv('RA_TLS_ALLOW_DEBUG_ENCLAVE_INSECURE', allow_debug_enclave_insecure)
    ra_tls_setenv('RA_TLS_MAA_PROVIDER_API_VERSION', maa_provider_api_version)

    ra_tls_verify_callback_der('maa', cert)

VERIFY_CB['maa'] = verify_maa
