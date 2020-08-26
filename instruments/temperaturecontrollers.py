import visa
import struct

__all__ = ['TEC1089SV']

class TEC1089SV:
    """
    All commands take the form #<address><sequence number><payload data><CRC16 checksum>
    the self.address class member contains both # and the 02 for address as shorthand
    and the payload data takes one of the following forms
    <operation><param id><instance><new value> for writing a value
    <operation><param id><instance> for reading a value
    <operation><instance> for a parameter less operation (e.g ?IF or ES)
    Everything is in ascii representation of hex (0-9,A-F) with no lowercase or extraneous characters.
    All error codes from the device contain a "+" followed by error code 00-09
    """

    def __init__(self):
        self.__CRC16_XMODEM_TABLE = [
            0x0000, 0x1021, 0x2042, 0x3063, 0x4084, 0x50a5, 0x60c6, 0x70e7,
            0x8108, 0x9129, 0xa14a, 0xb16b, 0xc18c, 0xd1ad, 0xe1ce, 0xf1ef,
            0x1231, 0x0210, 0x3273, 0x2252, 0x52b5, 0x4294, 0x72f7, 0x62d6,
            0x9339, 0x8318, 0xb37b, 0xa35a, 0xd3bd, 0xc39c, 0xf3ff, 0xe3de,
            0x2462, 0x3443, 0x0420, 0x1401, 0x64e6, 0x74c7, 0x44a4, 0x5485,
            0xa56a, 0xb54b, 0x8528, 0x9509, 0xe5ee, 0xf5cf, 0xc5ac, 0xd58d,
            0x3653, 0x2672, 0x1611, 0x0630, 0x76d7, 0x66f6, 0x5695, 0x46b4,
            0xb75b, 0xa77a, 0x9719, 0x8738, 0xf7df, 0xe7fe, 0xd79d, 0xc7bc,
            0x48c4, 0x58e5, 0x6886, 0x78a7, 0x0840, 0x1861, 0x2802, 0x3823,
            0xc9cc, 0xd9ed, 0xe98e, 0xf9af, 0x8948, 0x9969, 0xa90a, 0xb92b,
            0x5af5, 0x4ad4, 0x7ab7, 0x6a96, 0x1a71, 0x0a50, 0x3a33, 0x2a12,
            0xdbfd, 0xcbdc, 0xfbbf, 0xeb9e, 0x9b79, 0x8b58, 0xbb3b, 0xab1a,
            0x6ca6, 0x7c87, 0x4ce4, 0x5cc5, 0x2c22, 0x3c03, 0x0c60, 0x1c41,
            0xedae, 0xfd8f, 0xcdec, 0xddcd, 0xad2a, 0xbd0b, 0x8d68, 0x9d49,
            0x7e97, 0x6eb6, 0x5ed5, 0x4ef4, 0x3e13, 0x2e32, 0x1e51, 0x0e70,
            0xff9f, 0xefbe, 0xdfdd, 0xcffc, 0xbf1b, 0xaf3a, 0x9f59, 0x8f78,
            0x9188, 0x81a9, 0xb1ca, 0xa1eb, 0xd10c, 0xc12d, 0xf14e, 0xe16f,
            0x1080, 0x00a1, 0x30c2, 0x20e3, 0x5004, 0x4025, 0x7046, 0x6067,
            0x83b9, 0x9398, 0xa3fb, 0xb3da, 0xc33d, 0xd31c, 0xe37f, 0xf35e,
            0x02b1, 0x1290, 0x22f3, 0x32d2, 0x4235, 0x5214, 0x6277, 0x7256,
            0xb5ea, 0xa5cb, 0x95a8, 0x8589, 0xf56e, 0xe54f, 0xd52c, 0xc50d,
            0x34e2, 0x24c3, 0x14a0, 0x0481, 0x7466, 0x6447, 0x5424, 0x4405,
            0xa7db, 0xb7fa, 0x8799, 0x97b8, 0xe75f, 0xf77e, 0xc71d, 0xd73c,
            0x26d3, 0x36f2, 0x0691, 0x16b0, 0x6657, 0x7676, 0x4615, 0x5634,
            0xd94c, 0xc96d, 0xf90e, 0xe92f, 0x99c8, 0x89e9, 0xb98a, 0xa9ab,
            0x5844, 0x4865, 0x7806, 0x6827, 0x18c0, 0x08e1, 0x3882, 0x28a3,
            0xcb7d, 0xdb5c, 0xeb3f, 0xfb1e, 0x8bf9, 0x9bd8, 0xabbb, 0xbb9a,
            0x4a75, 0x5a54, 0x6a37, 0x7a16, 0x0af1, 0x1ad0, 0x2ab3, 0x3a92,
            0xfd2e, 0xed0f, 0xdd6c, 0xcd4d, 0xbdaa, 0xad8b, 0x9de8, 0x8dc9,
            0x7c26, 0x6c07, 0x5c64, 0x4c45, 0x3ca2, 0x2c83, 0x1ce0, 0x0cc1,
            0xef1f, 0xff3e, 0xcf5d, 0xdf7c, 0xaf9b, 0xbfba, 0x8fd9, 0x9ff8,
            0x6e17, 0x7e36, 0x4e55, 0x5e74, 0x2e93, 0x3eb2, 0x0ed1, 0x1ef0,
        ]
        self.__msg_counter = 0
        self.__address = '#02'

    def connect(self, port):
        rm = visa.ResourceManager('@ni')
        self.__tec = rm.open_resource(f'COM{port}', baud_rate=19200)
        self.__tec.close()
        self.__tec.open()
        self.__tec.baud_rate = 57600
        self.__tec.timeout = 10000
        self.__tec.write_termination = '\r'
        self.__tec.read_termination = '\r'
        print()
        self.__set_int32_param(108, 1)  # don't save data to flash
        self.__set_int32_param(50010, 1)  # ramp start point setting
        return self.get_identity()

    def stop(self):
        start = self.__address
        seq = self.__param_hex(self.__msg_counter)
        self.__msg_counter += 1
        op = 'ES'
        msg = start + seq + op
        response = self.__tec.query(msg + self.__crc16(msg.encode()))
        if '+' not in response:
            return response[7:-4]
        else:
            print('Failed to set value/read response with message:\n')
            print(response)

    def close(self):
        self.__tec.close()

    def get_object_temperature(self):
        return self.__hex_float32(self.__get_param(1000))

    def get_sink_temperature(self):
        return self.__hex_float32(self.__get_param(1001))

    def get_target_temperature(self):
        return self.__hex_float32(self.__get_param(3000))

    def get_output_current(self):
        return self.__hex_float32(self.__get_param(1020))

    def get_output_voltage(self):
        return self.__hex_float32(self.__get_param(1021))

    def set_target_temperature(self, target):
        return self.__set_float32_param(3000, float(target))

    def get_temp_stability_state(self):
        states = {0: 'off', 1: 'unstable', 2: 'stable'}
        return states[self.__hex_int(self.__get_param(1200))]

    def enable_control(self):
        """
        Enables temperature control. Use set_target_temperature first.
        :return:
        """
        return self.__set_int32_param(2010, 1)

    def disable_control(self):
        """
        Disables temperature control
        :return:
        """
        return self.__set_int32_param(2010, 0)

    def get_identity(self):
        """
        Reads the identity information from the instrument for printing on connect.
        :return:
        """
        start = self.__address
        seq = self.__param_hex(self.__msg_counter)
        self.__msg_counter += 1
        op = '?IF'
        msg = start + seq + op
        response = self.__tec.query(msg + self.__crc16(msg.encode()))
        if '+' not in response:
            return response[7:-4]
        else:
            print('Failed to set value/read response with message:\n')
            print(response)
        # 00ABCD?IF

    def __get_param(self, param):
        """

        :param int param: parameter ID
        :return: The message between the preamble and the checksum or None
        """
        start = self.__address
        seq = self.__param_hex(self.__msg_counter)
        self.__msg_counter += 1
        op = '?VR'
        param = self.__param_hex(param)
        instance = '01'
        msg = start + seq + op + param + instance
        response = self.__tec.query(msg + self.__crc16(msg.encode()))
        if '+' not in response:
            return response[7:-4]
        else:
            print('Failed to set value/read response with message:\n')
            print(response)

    def __set_int32_param(self, param, value):
        """

        :param param:
        :param value:
        :return:
        """
        start = self.__address
        seq = self.__param_hex(self.__msg_counter)
        self.__msg_counter += 1
        op = 'VS'
        param = self.__param_hex(param)
        instance = '01'
        val = self.__int32_hex(value)
        msg = start + seq + op + param + instance + val
        response = self.__tec.query(msg + self.__crc16(msg.encode()))
        if '+' not in response:
            return response[7:-4]
        else:
            print('Failed to set value/read response with message:\n')
            print(response)

    def __set_float32_param(self, param, value):
        """

        :param int param:
        :param float value:
        :return:
        """
        start = self.__address
        seq = self.__param_hex(self.__msg_counter)
        self.__msg_counter += 1
        op = 'VS'
        param = self.__param_hex(param)
        instance = '01'
        val = self.__float32_hex(value)
        msg = start + seq + op + param + instance + val
        response = self.__tec.query(msg + self.__crc16(msg.encode()))
        if '+' not in response:
            return response[7:-4]
        else:
            print('Failed to set value/read response with message:\n')
            print(response)

    def __param_hex(self, param):
        """
        Converts parameter number into hex form for use in queries etc.
        :param int param: the parameter number to be converted into hex
        :return: the hex form of the parameter number in 2byte format with no 0x prefix
        """
        return f"{param:04X}"

    def __int32_hex(self, value):
        """
        Convert int32 to hex for transmission to device
        :param int32 value: The value to be converted into a 32bit hex value
        :return: The string form of the hex with no 0x prefix, 8 characters long.
        """
        return f"{value:08X}"

    def __hex_int(self, hex_str):
        """
        Convert hex string from instrument into int32 (might not work with UInts above a large number)
        :param str hex_str:
        :return: integer from hex
        """
        return int(hex_str, 16)

    def __float32_hex(self, value):
        """
        Convert a python float to a hex string for sending to the device
        :param float value: value to be converted into float
        :return: hex string without 0x prefix
        """
        return hex(struct.unpack('<I', struct.pack('<f', value))[0]).lstrip('0x').upper()

    def __hex_float32(self, hex_str):
        """
        Convert hex output from device into usable numbers
        :param str hex_str: ascii hex representation of float to be converted
        :return: the float in double precision
        """
        return struct.unpack('!f', bytes.fromhex(hex_str))[0]

    def __crc16(self, data):
        """Calculate checksum using CRC16 (standard)
        :param string data: the entire message without CRC (inc the '#' at the start)
        :return: Return calculated value of CRC
        """
        crc = 0
        for byte in data:
            crc = ((crc << 8) & 0xFF00) ^ self.__CRC16_XMODEM_TABLE[((crc >> 8) & 0xFF) ^ byte]
        return '%X' % (crc & 0xFFFF)
