foreach d in fish airline ovary dollhill3 accident {
    capture webuse `d', clear
    if _rc==0 {
        display "DATASET `d' OK obs=" _N " vars=" r(k)
    }
    else {
        display "DATASET `d' FAILED rc=" _rc
    }
}
