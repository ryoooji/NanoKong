#ifndef WKPF_PROFILESH
#define WKPF_PROFILESH

#include "types.h"

#define WKPF_PROPERTY_TYPE_INT       0
#define WKPF_PROPERTY_TYPE_BOOLEAN   1
#define WKPF_PROPERTY_ACCESS_RO      (1 << 7)
#define WKPF_PROPERTY_ACCESS_WO      (1 << 6)
#define WKPF_PROPERTY_ACCESS_RW      WKPF_PROPERTY_ACCESS_RO+WKPF_PROPERTY_ACCESS_WO

typedef struct {
    uint16_t profile_id;
    void (*update) (void);
    void *java_object; // TODO: datatype?
    uint8_t number_of_properties;
    uint8_t *properties;
} wkpf_profile_definition;

extern uint8_t wkpf_register_profile(wkpf_profile_definition profile);
extern uint8_t wkpf_get_profile_by_id(uint16_t profile_id, wkpf_profile_definition **profile);
extern uint8_t wkpf_get_profile_by_index(uint8_t index, wkpf_profile_definition **profile);
extern uint8_t wkpf_get_number_of_profiles();


#endif // WKPF_PROFILESH