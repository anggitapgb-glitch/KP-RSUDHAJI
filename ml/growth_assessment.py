def assess_growth(bone_age_months, chronological_age_months):
    """
    Menghitung selisih usia dan memberikan penilaian klinis awal.
    """
    # Poin 6: Menghitung selisih usia tulang dengan usia kronologis
    selisih_bulan = bone_age_months - chronological_age_months
    
    # Poin 7: Penilaian awal pertumbuhan berdasarkan kriteria klinis
    # Secara klinis (acuan umum Greulich-Pyle), selisih lebih dari 12 bulan 
    # (1 tahun) sering dianggap signifikan, meski bisa disesuaikan lagi.
    if selisih_bulan > 12:
        kriteria = "Pertumbuhan Tulang Lanjut (Advanced Bone Age)"
        penjelasan = "Usia tulang lebih tua dari usia sebenarnya. Pertumbuhan kerangka lebih cepat dari rata-rata."
    elif selisih_bulan < -12:
        kriteria = "Pertumbuhan Tulang Terlambat (Delayed Bone Age)"
        penjelasan = "Usia tulang lebih muda dari usia sebenarnya. Pertumbuhan kerangka lebih lambat dari rata-rata."
    else:
        kriteria = "Pertumbuhan Normal"
        penjelasan = "Usia tulang sesuai dengan rentang usia kronologis pasien."
        
    return {
        "selisih_bulan": selisih_bulan,
        "kriteria": kriteria,
        "penjelasan": penjelasan
    }