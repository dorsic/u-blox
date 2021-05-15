{
 "metadata": {
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.7.3-final"
  },
  "orig_nbformat": 2,
  "kernelspec": {
   "name": "python3",
   "display_name": "Python 3.7.3 64-bit",
   "metadata": {
    "interpreter": {
     "hash": "31f2aee4e71d21fbe5cf8b01ff0e069b9275f58929596ceb00d14d90e3e16cd6"
    }
   }
  }
 },
 "nbformat": 4,
 "nbformat_minor": 2,
 "cells": [
  {
   "source": [
    "### READ BINARY UBX MESSAGES"
   ],
   "cell_type": "markdown",
   "metadata": {}
  },
  {
   "cell_type": "code",
   "execution_count": 6,
   "metadata": {},
   "outputs": [],
   "source": [
    "from pyubx2 import UBXReader\n",
    "import pyubx2"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 47,
   "metadata": {},
   "outputs": [
    {
     "output_type": "stream",
     "name": "stdout",
     "text": [
      "{'RXM-MEASX': 8851, 'RXM-RAWX': 8732, 'RXM-SFRBX': 93342, 'RXM-RLM': 17}\n"
     ]
    }
   ],
   "source": [
    "stream = open('/Users/dorsic/Development/github/u-blox/mms.ubx', 'rb')\n",
    "ubr = UBXReader(stream, True)\n",
    "cnt = {}\n",
    "for (raw_data, parsed_data) in ubr:\n",
    "    id = pyubx2.UBX_MSGIDS[parsed_data.msg_cls+parsed_data.msg_id]\n",
    "    cnt[id] = cnt[id] + 1 if id in cnt else 0\n",
    "\n",
    "print(cnt)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 48,
   "metadata": {},
   "outputs": [
    {
     "output_type": "execute_result",
     "data": {
      "text/plain": [
       "33067"
      ]
     },
     "metadata": {},
     "execution_count": 48
    }
   ],
   "source": [
    "msg.dopplerHz_02"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 56,
   "metadata": {},
   "outputs": [
    {
     "output_type": "execute_result",
     "data": {
      "text/plain": [
       "[b'\\xb5', b'b', b'\\r', b'\\x03']"
      ]
     },
     "metadata": {},
     "execution_count": 56
    }
   ],
   "source": [
    "a = b'\\x01\\x45\\xb5\\x62\\x0d\\x03\\x56'\n",
    "b = b'\\xb5\\x62\\x0d\\x03'\n",
    "[c.to_bytes(1, byteorder='big') for c in b]"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 57,
   "metadata": {},
   "outputs": [],
   "source": [
    "rtcm = [b'\\xD3' b'\\x00' b'\\x13' b'\\x3E' b'\\xD7' b'\\xD3' b'\\x02' b'\\x02' b'\\x98' b'\\x0E' b'\\xDE' b'\\xEF' b'\\x34' b'\\xB4' b'\\xBD' b'\\x62' b'\\xAC' b'\\x09' b'\\x41' b'\\x98' b'\\x6F' b'\\x33' b'\\x36' b'\\x0B' b'\\x98']\n",
    "\n",
    "with open(\"/Users/dorsic/Downloads/sample.rtcm3\", 'wb') as f:\n",
    "    for b in rtcm:\n",
    "        f.write(b)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 76,
   "metadata": {},
   "outputs": [
    {
     "output_type": "execute_result",
     "data": {
      "text/plain": [
       "211"
      ]
     },
     "metadata": {},
     "execution_count": 76
    }
   ],
   "source": [
    "a29 = [211, 0, 8, 76, 224, 0, 138, 0, 0, 0, 0, 168, 247, 42]\n",
    "a30 = [211, 0, 62, 254, 128, 1, 0, 0, 0, 24, 66, 71, 220, 0, 0, 0, 8, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 3, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 5, 1, 0, 0, 0, 0, 5, 2, 0, 0, 0, 0, 5, 3, 0, 0, 0, 0, 122, 243, 29]\n"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 75,
   "metadata": {},
   "outputs": [
    {
     "output_type": "execute_result",
     "data": {
      "text/plain": [
       "b'\\xd3*'"
      ]
     },
     "metadata": {},
     "execution_count": 75
    }
   ],
   "source": [
    "a = [211, 42]\n",
    "b''.join([x.to_bytes(1, byteorder='big') for x in a])\n"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": []
  }
 ]
}