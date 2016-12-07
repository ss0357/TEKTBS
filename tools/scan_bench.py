import visa
rm = visa.ResourceManager()
import time


bench_id = 1
name = {
    'Q010010': 31,
    'C010027': 32,
    'C010003': 33,
    'C010011': 34,
    'C010008': 35
}

for i in range(101,112):
    ipadd = '192.168.0.%d' % i
    res_expr = 'TCPIP0::%s::INSTR' % ipadd
    print ("========================================")
    print (i, res_expr)
    try:
        inst = rm.open_resource(res_expr, timeout=10)
        print(inst.query("*IDN?"))
        idn = inst.query("*IDN?")
        scope_type = idn.split(',')[1]
        scope_serial = idn.split(',')[2]
        if scope_serial in name:
            hostid = name[scope_serial]
        else:
            hostid = bench_id
            bench_id += 1

        inst.write(":ethernet:name \"Bench%d\"" % hostid)
        time.sleep(2)
        print(inst.query("ethernet:name?"))
        inst.close()

        print('===> Bench%d    %s    %s  %s' % (hostid, ipadd, scope_type, scope_serial))

    except Exception as e:
        print ("Exception:", e)
        print('failed to connect %s' % res_expr)