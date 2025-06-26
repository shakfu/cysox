#!/usr/bin/env python
#
# use multiprocessing to process 2 chains
# transport via socket sent_bytes (even better efficiency without pickling bytearrays)
#
# $Id: example12-multiprocess.py 96 2011-03-27 16:02:44Z patrick $
#
# Copyright 2011 Patrick Atamaniuk
#
# This source code is freely redistributable and may be used for
# any purpose.  This copyright notice must be maintained.
# Patrick Atamaniuk and Contributors are not responsible for
# the consequences of using this software.
#
from multiprocessing import Process, Pipe
import pysox
from pysox.sox import PY3

class IEffs(pysox.CCustomEffect):
    """generate audio"""
    junks=3
    sample=4
    def drain(self, buffer_object):
        """create a few samples"""
        if 0 == self.junks:
            return 0
        self.junks -= 1
        l = 3
        for i in range(l):
            print('generating sample ',self.sample)
            buffer_object[i*2] = self.sample
            buffer_object[i*2+1] = -self.sample
            self.sample -= 1
        return l*2

class OEffs(pysox.CCustomEffect):
    """write audio to socket in binary bytes format"""
    conn = None
    def set_send_channel(self, conn):
        self.conn = conn
    def flow(self, ibuf, obuf, isamp):
        """read from ibuf and end the chain by providing 0 output
        send output to socket"""
        print("OEffs flow", isamp, len(ibuf))
#        ibuf.set_readonly()
        try:
            if self.conn:
                if not len(ibuf):
                    return 0
                if PY3:
                    self.conn.send_bytes(ibuf)
                else: #WTF???
                    self.conn.send_bytes(bytes(ibuf.tobytearray()))
                return 0
        except Exception as e:
            print("Exception",e)
            import traceback
            traceback.print_exc()
        return 0 #0 samples put in obuf, we are end of chain
    
    def stop(self):
        if self.conn:
            self.conn.send_bytes(b'')
            self.conn.close()
            self.conn = None
        return 0

class IEffr(pysox.CCustomEffect):
    """read audio from socket in binary bytes format"""
    conn = None
    def set_recv_channel(self, conn):
        self.conn = conn

    def drain(self, buf):
        """receive input from socket"""
        print("IEffr drain")
        if self.conn:
            try:
                #directly receive the data into the buffer
                b = self.conn.recv_bytes_into(buf)
                #inform our buffer what amount of valid data it now contains
                #so it can iterate or export it without trailing junk
                buf.set_datalen(b)
            except EOFError:
                print("EOF")
                return 0
#
# Second variant, involving a bytes intermediate object
#            b = self.conn.recv_bytes()
#            if not b or not len(b):
#                print("IEffr drain stop")
#                self.conn.close()
#                return 0
#            buf.writebytes(b)
            print('IEffr check',buf.tolist())
            return len(buf)
        print("IEffr drain end")
        return 0


class OEffr(pysox.CCustomEffect):
    """write audio to stdout"""
    def flow(self, ibuf, obuf, isamp):
        """read from ibuf and end the chain by providing 0 output"""
        print("OEffr flow", isamp, len(ibuf))
        print('OEffr check',ibuf.tolist())
        return 0 #0 samples put in obuf, we are end of chain
    
def mainchain(conn):
    """read audio from socket and write to stdout"""
    output = OEffr("output", [])
    input = IEffr("input", [])
    input.set_recv_channel(conn)
    input.get_out_signal().set_param(rate=44100, channels=2, precision=32)
    chain = pysox.CEffectsChain()
    chain.add_effect(input)
    chain.add_effect(output)
    chain.flow_effects()
    print("mainchain done.")


def subchain(conn):
    """generate audio and send to socket"""
    output = OEffs("output", [])
    output.set_send_channel(conn)
    input = IEffs("input", [])
    input.get_out_signal().set_param(rate=44100, channels=2, precision=32)
    chain = pysox.CEffectsChain()
    chain.add_effect(input)
    chain.add_effect(output)
    chain.flow_effects()
    print("subchain done.")
    
if __name__ == '__main__':
    parent_conn, child_conn = Pipe()
    p = Process(target=subchain, args=(child_conn, ))
    p.start()
    mainchain(parent_conn)
    p.join()

