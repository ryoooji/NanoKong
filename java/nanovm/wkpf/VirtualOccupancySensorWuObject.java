package nanovm.wkpf;

public class VirtualOccupancySensorWuObject extends VirtualWuObject {
    public static final byte[] properties = new byte[] {
            WKPF.PROPERTY_TYPE_BOOLEAN|WKPF.PROPERTY_ACCESS_RW // PROPERTY_OCCUPANCY_SENSOR_OCCUPIED
    };

    public static final short WUCLASS_OCCUPANCY_SENSOR                           = 0x1005;
    public static final byte PROPERTY_OCCUPANCY_SENSOR_OCCUPIED                  = 0;

    public void update() {
      System.out.println("WKPFUPDATE(OccupancySensor): NOP");
      return;
    }
}
