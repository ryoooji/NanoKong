import nanovm.avr.*;
import nanovm.io.*;

class IntelDemoLightSensorV1 {
  private static final short COMMAND_SET_LAMP = 1;
  private static final short COMMAND_SET_THRESHOLD = 2;
  private static final short COMMAND_GET_STATUS = 3;
  private static final short COMMAND_GET_STATUS_REPLY = 4;

  private static final short COMMAND_SET_LAMP_ACK = 11;
  private static final short COMMAND_SET_THRESHOLD_ACK = 12;

  private static final byte BASESTATION_ID = 2;
  private static final byte LAMP_NODE_ID = 3;

  private static final short INITIAL_THRESHOLD = 240;

  private static boolean setLight(boolean turn_on) {
    if(turn_on) {
      NvmComm.send(LAMP_NODE_ID, new byte[] {COMMAND_SET_LAMP, 1}, (byte)2);
      System.out.println("Sending 'lamp on' command");
    }
    else {
      NvmComm.send(LAMP_NODE_ID, new byte[] {COMMAND_SET_LAMP, 0}, (byte)2);
      System.out.println("Sending 'lamp off' command");
    }
    byte[] data = NvmComm.receive(100);
    if (data != null && data.length == 1 && data[0] == COMMAND_SET_LAMP_ACK)
      return true;
    else
      return false;
  }

  public static void main(String[] args) {
    int threshold = INITIAL_THRESHOLD;
    int light_sensor_reading = 255;
    int lamp_on = -1;

    Adc.setPrescaler(Adc.DIV64);
    Adc.setReference(Adc.INTERNAL);

    while(true) {
      byte[] data = NvmComm.receive(1000);
        if (data != null) {
          if (data.length == 2 && data[0] == COMMAND_SET_THRESHOLD) {
            threshold = 0xFF & data[1]; // necessary since Java doesn't have unsigned bytes
            byte[] reply = new byte[] {COMMAND_SET_THRESHOLD_ACK};
            NvmComm.send((byte)BASESTATION_ID, reply, (byte)1);
            System.out.println("Set threshold to " + threshold);
          } else if (data.length == 1 && data[0] == COMMAND_GET_STATUS) {
            System.out.println("Sending GET_STATUS_REPLY");
            byte[] reply = new byte[] {COMMAND_GET_STATUS_REPLY,
                                       (byte)threshold,
                                       (byte)light_sensor_reading,
                                       (byte)lamp_on};
            NvmComm.send((byte)BASESTATION_ID, reply, (byte)4);
          }
        }
        light_sensor_reading = Adc.getByte(Adc.CHANNEL15);
        System.out.println("Sensed value:" + light_sensor_reading);
        System.out.println("Threshold:" + threshold);
        if (lamp_on==1)
          System.out.println("Lamp: On");
        else if (lamp_on==0)
          System.out.println("Lamp: Off");
        if (light_sensor_reading <= threshold && lamp_on != 1) {
            if (setLight(true))
              lamp_on = 1;
        }
        if (light_sensor_reading > threshold && lamp_on != 0) {
            if (setLight(false))
              lamp_on = 0;
        }
    }
  }
}
