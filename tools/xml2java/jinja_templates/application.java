import java.io.*;
import nanovm.avr.*;
import nanovm.wkpf.*;
import nanovm.lang.Math;

public class {{ applicationName }} {

    // =========== Begin: Generated by the translator from application WuML
    /* Component instance IDs to indexes:
    {%- for instance in wuObjects %}
    {{ instance.getWuClass().getName() }} => {{ instance.getInstanceIndex() }}
    {%- endfor %}
    */

    //link table
    // fromInstanceIndex(2 bytes), fromPropertyId(1 byte), toInstanceIndex(2 bytes), toPropertyId(1 byte), toWuClassId(2 bytes)
    //eg. (byte)0,(byte)0, (byte)0, (byte)2,(byte)0, (byte)1, (byte)1,(byte)0
    private final static byte[] linkDefinitions = {
        // Note: Component instance id and wuclass id are little endian
        // Note: using WKPF constants now, but this should be generated as literal bytes by the WuML->Java compiler.
        // Connect input controller to threshold
        {%- for link in wuLinks %}
            {{ link.toJava() }}{{ ',' if not loop.last else '' }}
        {%- endfor %}
    };

    //component node id and port number table
    // each row corresponds to the component index mapped from component ID above
    // each row has two items: node id, port number
    private final static byte[] componentInstanceToWuObjectAddrMap = {
        {%- for wuobject in wuObjects %}
        {{ wuobject.toJava() }}{{ ',' if not loop.last else '' }}
        {%- endfor %}
    };
    // =========== End: Generated by the translator from application WuML

    public static void main (String[] args) {
        System.out.println("{{ applicationName }}");
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

    private static void initialiseLocalWuObjects() {
        {%- for object in wuObjects %}

        if (WKPF.isLocalComponent((short){{ object.getInstanceIndex() }})) {

        {%- if object.getWuClass().isVirtual() %}

        // Virtual WuClasses (Java)
        VirtualWuObject wuclassInstance{{ object.getWuClassName() }} = new {{ object.getWuClass().getJavaClassName() }}();
        WKPF.registerWuClass(WKPF.{{ object.getWuClass().getJavaConstName() }}, {{ object.getWuClass().getJavaGenClassName() }}.properties);
        WKPF.createWuObject((short)WKPF.{{ object.getWuClass().getJavaConstName() }}, WKPF.getPortNumberForComponent((short){{ object.getInstanceIndex() }}), wuclassInstance{{ object.getWuClassName() }});
        {% for property in object -%}
            {%- if property.hasDefault() -%}
                {%- if property.getDataType() == 'boolean' -%}
                WKPF.setPropertyBoolean(wuclassInstance{{ object.getWuClassName() }}, WKPF.{{ property.getJavaConstName() }}, {{ property.getDefault().lower() }});
                {%- elif property.getDataType() == 'int' -%}
                WKPF.setPropertyShort(wuclassInstance{{ object.getWuClassName() }}, WKPF.{{ property.getJavaConstName() }}, (short){{ property.getDefault() }});
                {%- elif property.getDataType() == 'short' -%}
                WKPF.setPropertyShort(wuclassInstance{{ object.getWuClassName() }}, WKPF.{{ property.getJavaConstName() }}, (short){{ property.getDefault() }});
                {%- elif property.getDataType() == 'refresh_rate' -%}
                WKPF.setPropertyRefreshRate(wuclassInstance{{ object.getWuClassName() }}, WKPF.{{ property.getJavaConstName() }}, (short){{ property.getDefault() }});
                {%- else -%}
                WKPF.setPropertyShort(wuclassInstance{{ object.getWuClassName() }}, WKPF.{{ property.getJavaConstName() }}, WKPF.{{ property.getWuType().getValueInJavaConstant(property.getDefault()) }});
                {%- endif -%}
            {%- endif %}
        {% endfor %}

        {% else %}

        // Native WuClasses (C)
        WKPF.createWuObject((short)WKPF.{{ object.getWuClass().getJavaConstName() }}, WKPF.getPortNumberForComponent((short){{ object.getInstanceIndex() }}), null);
        {%- for property in object -%}
            {%- if property.hasDefault() -%}
                {%- if property.getDataType() == 'boolean' -%}
                WKPF.setPropertyBoolean((short){{ object.getInstanceIndex() }}, WKPF.{{ property.getJavaConstName() }}, {{ property.getDefault().lower() }});
                {%- elif property.getDataType() == 'int' -%}
                WKPF.setPropertyShort((short){{ object.getInstanceIndex() }}, WKPF.{{ property.getJavaConstName() }}, (short){{ property.getDefault() }});
                {%- elif property.getDataType() == 'short' -%}
                WKPF.setPropertyShort((short){{ object.getInstanceIndex() }}, WKPF.{{ property.getJavaConstName() }}, (short){{ property.getDefault() }});
                {%- elif property.getDataType() == 'refresh_rate' -%}
                WKPF.setPropertyRefreshRate((short){{ object.getInstanceIndex() }}, WKPF.{{ property.getJavaConstName() }}, (short){{ property.getDefault() }});
                {%- else -%}
                WKPF.setPropertyShort((short){{ object.getInstanceIndex() }}, WKPF.{{ property.getJavaConstName() }}, WKPF.{{ property.getWuType().getValueInJavaConstant(property.getDefault()) }});
                {%- endif -%}
            {%- endif %}
        {% endfor %}
        {%- endif -%}

        }

        {%- endfor %}
    }
}
