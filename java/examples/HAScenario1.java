//========== Components Definitions ==========
// 0 InputController1 {'classid': 3, 'defaults': [(u'output', 127)], 'class': u'Numeric_Controller', 'cmpid': 0}
// 1 LightSensor1 {'classid': 5, 'defaults': [(u'refresh_rate', ('r', 1000))], 'class': u'Light_Sensor', 'cmpid': 1}
// 2 Threshold1 {'classid': 1, 'defaults': [(u'operator', u'WKPF.ENUM_THRESHOLD_OPERATOR_LTE')], 'class': u'Threshold', 'cmpid': 2}
// 3 Light1 {'classid': 4, 'defaults': [], 'class': u'Light', 'cmpid': 3}
//
//========== Links Definitions ==========
// fromCompInstanceId(2 bytes), fromPropertyId(1 byte), toCompInstanceId(2 bytes), toPropertyId(1 byte), toWuClassId(2 bytes)
// (u'InputController1', u'output', u'Threshold1', u'threshold', u'Threshold1')
// (0, 0) 0 (2, 0) 1 (1, 0)
// (u'LightSensor1', u'current_value', u'Threshold1', u'value', u'Threshold1')
// (1, 0) 0 (2, 0) 2 (1, 0)
// (u'Threshold1', u'output', u'Light1', u'on_off', u'Light1')
// (2, 0) 3 (3, 0) 0 (4, 0)
//
//========== Code ==========
import java.io.*;
import nanovm.avr.*;
import nanovm.wkpf.*;
import nanovm.lang.Math;

public class HAScenario1 {
    public static void main (String[] args) {
        System.out.println("HAScenario1");
        WKPF.loadComponentToWuObjectAddrMap(componentInstanceToWuObjectAddrMap);
        WKPF.loadLinkDefinitions(linkDefinitions);
        initialiseLocalWuObjects();
        
        while(true){
            VirtualWuObject wuclass = WKPF.select();
            if (wuclass != null) {
                wuclass.update();
            }
        }
    }

    private final static byte[] linkDefinitions = {
        (byte)0,(byte)0, (byte)0,  (byte)2,(byte)0, (byte)1,  (byte)1, (byte)0,
        (byte)1,(byte)0, (byte)0,  (byte)2,(byte)0, (byte)2,  (byte)1, (byte)0,
        (byte)2,(byte)0, (byte)3,  (byte)3,(byte)0, (byte)0,  (byte)4, (byte)0,
    };

    private final static byte[] componentInstanceToWuObjectAddrMap = {
        (byte)1, (byte)1, 
        (byte)1, (byte)2, 
        (byte)3, (byte)1, 
        (byte)3, (byte)4, 
    };

    private static void initialiseLocalWuObjects() {
        if (WKPF.isLocalComponent((short)0)) {
            WKPF.setPropertyShort((short)0, WKPF.PROPERTY_NUMERIC_CONTROLLER_OUTPUT, (short)127);
        }
        if (WKPF.isLocalComponent((short)1)) {
            WKPF.setPropertyRefreshRate((short)1, WKPF.PROPERTY_LIGHT_SENSOR_REFRESH_RATE, (short)1000);
        }
        if (WKPF.isLocalComponent((short)2)) {
            WKPF.createWuObject((short)WKPF.WUCLASS_THRESHOLD, WKPF.getPortNumberForComponent((short)2), null);
            WKPF.setPropertyShort((short)2, WKPF.PROPERTY_THRESHOLD_OPERATOR, WKPF.ENUM_THRESHOLD_OPERATOR_LTE);
        }
        // no need to init component 3
    }
}
    
