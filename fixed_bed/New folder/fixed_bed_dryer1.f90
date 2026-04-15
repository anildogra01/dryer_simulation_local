program fixed_bed_dryer
    !-------------------------------------------------------------------
    ! FIXED BED DRYER SIMULATION
    !-------------------------------------------------------------------
    IMPLICIT NONE
    use PsyFun
    use emc_grain
    implicit none
    ! Header variables (ADD THESE)
    CHARACTER(LEN=100) :: user_name
    CHARACTER(LEN=100) :: project_name
    CHARACTER(LEN=200) :: address
    CHARACTER(LEN=50) :: crop_name
    CHARACTER(LEN=50) :: simulation_date
    
    ! Common block variables
    real :: xmt, tht, rht, delt, cfm, xmo
    integer :: kab
    real :: sa, ca, cp, cv, cw, rhop, hfg
    character(len=10) :: iname, iprod
    
    common /main/ xmt, tht, rht, delt, cfm, xmo, kab
    common /prprty/ sa, ca, cp, cv, cw, rhop, hfg
    common /mame/ iname, iprod
    
    ! Local arrays
    real :: xm(150), th(150), rh(151), t(151,2), h(151,2), deep(20)
    
    ! Local variables
    real :: rhc, d, prt, time, tbtpr, xmend
    integer :: iterct, iexit, jk, kcon
    real :: thin, tin, hin, depth, delx, dbtpr, rhin, ga, hc, xme
    real :: con1, con2, con3, con4, con5, con6, con7
    real :: scon1, scon2, scon3, tmth, ht, tabs, twba, hs, sum, xmave
    real :: pkcon, pkab, energy, water, btuh20, tt
    real :: indpr_real, nlpf_real  ! Read as real, convert to integer
    integer :: indpr, nlpf, ind, indi, i, ip1, j, jm, jr, nodes
    
    ! Initialize constants
    rhc = 0.9999999999
    d = 0.0
    prt = 0.0
    time = 0.0
    iterct = 0
    iexit = 0
    jk = 0
    kcon = 0
    kab = 0
    
    ! Initialize properties
    sa = 239.0
    ca = 0.242
    cp = 0.268
    cv = 0.45
    cw = 1.0
    rhop = 38.71
    hfg = 1000.0
    patm = 14.30
    
    ! Set product name
    iname = 'THOMPSON  '
    iprod = ' CORN     '
    
    ! Open input and output files
    write(*,*) 'Opening FIXED.DAT...'
    open(unit=5, file='FIXED.DAT', status='old', action='read', err=999)
    open(unit=6, file='FIXED.OUT', status='replace', action='write')
    
    write(*,*) 'Reading input parameters...'

    ! ============================================================
    ! READ ALL INPUT (text first, then numbers)
    ! ============================================================
    write(*,*) 'Reading input parameters...'
    
    ! Read header information (5 text lines)
    read(5, '(A)') user_name
    read(5, '(A)') project_name
    read(5, '(A)') address
    read(5, '(A)') crop_name
    read(5, '(A)') simulation_date
    ! Input conditions of dryer to be simulated
    read(5, *) xmo, thin, tin, hin, cfm
    read(5, *) depth, indpr_real
    read(5, *) nlpf_real, tt
    read(5, *) tbtpr, xmend
    
    ! Convert to integers
    indpr = int(indpr_real)
    nlpf = int(nlpf_real)
    
    write(*,*) 'Input read successfully:'
    write(*,*) '  XMO   =', xmo
    write(*,*) '  THIN  =', thin
    write(*,*) '  TIN   =', tin
    write(*,*) '  DEPTH =', depth
    write(*,*) '  TT    =', tt
    
    ! Compute step size, number of nodes and depth between prints
    delx = 1.0 / real(nlpf)
    ind = int(nlpf * depth)
    indi = ind + 1
    dbtpr = real(indpr) * delx
    
    write(*,*) 'Grid created:'
    write(*,*) '  Nodes =', ind
    write(*,*) '  DELX  =', delx
    
    ! Compute output depths for printing
    jk = 0
    do i = 1, indi, indpr
        jk = jk + 1
        deep(jk) = d
        d = d + dbtpr
    end do
    
    ! Compute inlet RH and initialize all array positions necessary
    rhin = rhdbha(f_temp(tin), hin)
    
    write(*,*) 'Initializing arrays...'
    do i = 1, ind
        ip1 = i + 1
        xm(i) = xmo
        th(i) = thin
        h(ip1,1) = hin
        h(ip1,2) = hin
        t(ip1,1) = tin
        t(ip1,2) = tin
        rh(ip1) = rhin
    end do
    
    t(1,1) = tin
    t(1,2) = tin
    h(1,1) = hin
    h(1,2) = hin
    rh(1) = rhin
    th(1) = (tin + thin) / 2.0
    
    ! Convert airflow to lb/hr and compute convective heat transfer
    ga = 60.0 * cfm / vsdbha(f_temp(thin), hin)
    
    if (ga >= 500.0) then
        hc = 0.363 * ga**0.59
    else
        hc = 0.69 * ga**0.49
    end if
    
    xme = emc(rhin, tin)
    
    write(*,*) 'Computed properties:'
    write(*,*) '  GA    =', ga, ' lb/hr'
    write(*,*) '  HC    =', hc, ' BTU/hr-ft2-F'
    write(*,*) '  XME   =', xme
    
    ! Print header page of conditions and properties
    write(6, 210) iname, iprod, tin, thin, rhin, hin, xmo, xme, cfm, ga, &
                  ca, cp, cv, cw, hc, patm, hfg, rhop, sa, depth, delx, &
                  dbtpr, tt, tbtpr, xmend
    
    ! Print depths for which output corresponds
    write(6, 211) (deep(i), i = 1, jk)
    
    ! Compute constants used by equations within loop
    con1 = 2.0 * ga * ca
    con2 = 2.0 * ga * cv
    con3 = hc * sa * delx
    con4 = rhop * cp
    con5 = rhop * cw
    con6 = 2.0 * con3
    con7 = ga * (ca + cv * hin) * (tin - thin)
    
    write(*,*) 'Starting time loop...'
    
    !===================================================================
    ! BEGIN TIME LOOP
    !===================================================================
    do while (iexit == 0)
        
        ! Compute size of this time step
        delt = 2.0 * delx * (con4 + con5 * xm(1)) / &
               (con1 + con2 * h(indi,1)) * 0.9
        time = time + delt
        scon1 = ga * delt / delx
        scon2 = rhop / scon1
        scon3 = hc * sa * delt
        
        !---------------------------------------------------------------
        ! BEGIN DEPTH LOOP
        !---------------------------------------------------------------
        do j = 2, indi
            jm = j - 1
            tht = (th(jm) + t(jm,2)) / 2.0
            xmt = xm(jm)
            
            ! Skip the theta equation on the first time step
            if (iterct > 0) then
                if (xmt < 0.17) then
                    hfg = (1094.0 - 0.57 * tht) * (1.0 + 4.349 * exp(-28.25 * xmt))
                end if
                
                tmth = (t(jm,1) + t(j,1)) / 2.0 - th(jm)
                
                ! Theta equation
                th(jm) = th(jm) + scon3 * tmth - &
                         (hfg + cv * tmth) * scon1 * (h(j,1) - h(jm,1)) / &
                         (con4 + con5 * xmt)
                
                tht = (th(jm) + t(jm,2)) / 2.0
            else
                tht = (t(jm,2) + 2.0 * t(jm,1) + t(j,1)) / 4.0
            end if
            
            ht = ((h(jm,1) + h(j,1)) / 2.0 + h(jm,2)) / 2.0
            rht = rhdbha(f_temp(tht), ht)
            
            ! Call subroutine containing M equation
            call layer()
            
            hfg = 1000.0
            
            ! H equation
            h(j,2) = h(jm,2) - scon2 * (xmt - xm(jm))
            ht = (h(jm,2) + h(j,2)) / 2.0
            
            ! T equation
            t(j,2) = (t(jm,2) * (con1 + con2 * ht - con3) + th(jm) * con6) / &
                     (con1 + con2 * ht + con3)
            tabs = f_temp(t(j,2))
            
            ! Compute RH and check for condensation
            rh(j) = rhdbha(tabs, h(j,2))
            
            if (rh(j) >= rhc) then
                ! Condensation simulator
                twba = wbdbhas(tabs, h(j,2), tabs, tabs + 20.0, 0.01)
                hs = h(j,2)
                
                t(j,2) = twba - 459.69
                h(j,2) = hadbrh(twba, rhc)
                rh(j) = rhc
                kcon = kcon + 1
                xmt = xmt + (hs - h(j,2)) / scon2
            end if
            
            xm(jm) = xmt
            
        end do  ! End depth loop
        
        sum = 0.0
        
        ! Shift and compute average moisture content
        do j = 2, indi
            t(j,1) = t(j,2)
            h(j,1) = h(j,2)
            sum = sum + xm(j-1)
        end do
        
        xmave = sum / real(ind)
        iterct = iterct + 1
        nodes = ind * iterct
        pkcon = real(kcon) * 100.0 / real(nodes)
        pkab = real(kab) * 100.0 / real(nodes)
        
        ! Check if time to print or end
        if (time >= prt .or. iexit == 1) then
            ! Final calculations and print
            energy = con7 * time
            water = (xmo - xmave) * rhop * depth
            if (water > 0.0) then
                btuh20 = energy / water
            else
                btuh20 = 0.0
            end if
            
            write(6, 212) time, pkcon, pkab, xmave, energy, water, btuh20
            write(6, 213) (t(i,2), i = 1, indi, indpr)
            write(6, 214) th(1), (th(i), i = indpr, ind, indpr)
            write(6, 215) xm(1), (xm(i), i = indpr, ind, indpr)
            write(6, 216) (rh(i), i = 1, indi, indpr)
            write(6, 217) (h(i,2), i = 1, indi, indpr)
            
            write(*,'(a,f8.2,a,f8.4)') '  Time =', time, '  Avg MC =', xmave
            
            prt = prt + tbtpr
        end if
        
        ! Check exit conditions
        if ((time + delt) >= tt) then
            iexit = 1
        else if (xmave <= xmend) then
            iexit = 1
        end if
        
    end do  ! End time loop
    
    ! Close files
    close(5)
    close(6)
    
    write(*,*) ''
    write(*,*) 'Simulation complete!'
    write(*,*) 'Results written to FIXED.OUT'
    write(*,*) 'Final average MC =', xmave
    write(*,*) 'Total time =', time, ' hours'
    
    stop
    
999 write(*,*) 'ERROR: Cannot open FIXED.DAT'
    write(*,*) 'Make sure FIXED.DAT is in the same directory as the program'
    stop
    
    !===================================================================
    ! FORMAT STATEMENTS
    !===================================================================
210 format(1h1, 43x, '               U S E R  N A M E               ', &
           /33x, '               A D D R S S   O F   U S E R                '&
           /42x, 'F I X E D  B E D  D R Y E R  M O D E L', /59x, 'U S I N G  T H E', &
           /44x, a10, ' THINLAYER EQUATION FOR', a10, 10(/), &
           52x, 'INPUT PROPERTIES AND CONDITIONS', 5(/), &
           '  AIR TEMP(DEG F)  PROD TEMP(DEG F)   REL HUM(DECIMAL)    ABS HUM(LB/LB)', &
           '   DB MC(DECIMAL) EQUIL MC(DECIMAL) AIR FLOW RATE (CFM)', &
           /1x, 7(5x, f9.4, 5x), /20x, f9.4, ' (LB/HR)', &
           4(/), 11x, 'HEAT CAPACITIES(BTU/LB)', 14x, 'AIR', 14x, 'PRODUCT', 10x, &
           'WATER VAPOR', 8x, 'WATER LIQUID', /34x, 4(13x, f6.4), 5(/), &
           24x, 'H T COEF CONV', 7x, 'ATMOS PRESS', 6x, 'LAT HEAT EVAP', 4x, &
           'BULK DENS DRY PROD', 3x, 'SPEC SURF AREA', /14x, 5(10x, f9.4), 10(/), &
           60x, 'PROGRAM CONTROLS', 5(/), 29x, 'SIMULATE A DEPTH OF', f6.2, &
           ' FT BY INCREMENTS OF', f7.4, ' FT PRINTING EVERY', f5.2, ' FT', &
           /29x, 'FOR A TOTAL TIME OF', f6.2, ' HR PRINTING EVERY', f5.2, ' HR', &
           /29x, 'OR UNTIL THE AVERAGE MC FALLS BELOW', f8.6)
211 format('0DEPTH', 15f8.2)
212 format('0TIME =', f6.2, 31x, 'PERCENT CONDENSATION =', f6.2, 15x, &
           'PERCENT ABSORPTION =', f6.2, /6x, 'AVERAGE MC =', f6.4, 14x, &
           'ENERGY INPUT =', f8.2, 10x, 'H20 REMOVED =', f7.2, 13x, 'BTU/LBH20 =', f8.2)
213 format('0AIR TEMP', 15f8.3)
214 format('0PROD TEMP', f7.3, 14f8.3)
215 format('0MC DB', f7.3, 14f8.3)
216 format('0REL HUM', 15f8.5)
217 format('0ABS HUM', 15f8.5)
    
contains

    real function f_temp(t)
        real, intent(in) :: t
        f_temp = t + 459.69
    end function f_temp

end program fixed_bed_dryer


!-----------------------------------------------------------------------
! LAYER - Thompson's thin-layer drying equation
!-----------------------------------------------------------------------
subroutine layer()
    implicit none
    
    ! Common blocks
    real :: xmt, tht, rht, delt, cfm, xmo
    integer :: kab
    real :: sa, ca, cp, cv, cw, rhop, hfg
    
    common /main/ xmt, tht, rht, delt, cfm, xmo, kab
    common /prprty/ sa, ca, cp, cv, cw, rhop, hfg
    
    ! Local variables
    real :: a, b, xme, xmr, almr, ti, rad, gvel
    
    ! Thompson equation parameters (for corn)
    a = -1.86178 + 0.0048843 * tht
    b = 427.364 * exp(-0.03301 * tht)
    
    ! Equilibrium moisture content
    ! Using simplified correlation for now
    if (rht >= 1.0) then
        xme = xmt  ! Prevent absorption
    else if (rht < 0.01) then
        xme = 0.05
    else
        ! Approximate EMC based on RH and temperature
        xme = 0.05 + 0.20 * rht
        if (xme > xmt) xme = xmt  ! Prevent absorption
    end if
    
    ! Moisture ratio
    if (xmo > xme) then
        xmr = (xmt - xme) / (xmo - xme)
    else
        xmr = 0.01
    end if
    
    ! Prevent negative or zero moisture ratio
    if (xmr <= 0.0) then
        xmr = 0.01
        kab = kab + 1
    end if
    
    almr = log(xmr)
    
    ! Compute equivalent time
    ti = almr * (a + b * almr)
    rad = sqrt(abs(a * a + 4.0 * b * ti))
    
    ! Grain velocity (approximate for fixed bed - very slow)
    gvel = 0.01  ! Very slow movement in fixed bed
    
    ! dM/dt equation (Thompson)
    if (rad > 0.0) then
        xmt = xmt - (xmo - xme) / gvel * exp((-a - rad) / (b * b)) / rad * delt
    end if
    
    ! Prevent MC from going below equilibrium or negative
    if (xmt < xme) xmt = xme
    if (xmt < 0.0) xmt = 0.0
    
end subroutine layer
