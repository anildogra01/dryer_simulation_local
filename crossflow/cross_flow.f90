program crossflow_dryer
    !-------------------------------------------------------------------
    ! CROSSFLOW GRAIN DRYER MODEL
    !
    ! Michigan State University
    ! Agricultural Engineering Department
    ! F.W. Bakker-Arkema, Project Leader
    ! L.E. Lerew, Programmer
    !
    ! Description:
    !   Main program for simulation of a crossflow dryer
    !
    ! Subroutines:
    !   - LAYER - Thin-layer drying equation
    !
    ! Functions:
    !   - EMC - Equilibrium moisture content
    !   - SYCHART PACKAGE - Psychrometric functions
    !-------------------------------------------------------------------
    use sychart_package
    use emc_corn
    implicit none
    
    ! Common blocks
    real :: xmt, tht, rht, delt, cfm, xmo
    integer :: kab
    real :: sa, ca, cp, cv, cw, rhop, hfg
    character(len=10) :: iname, iprod
    
    common /main/ xmt, tht, rht, delt, cfm, xmo, kab
    common /prprty/ sa, ca, cp, cv, cw, rhop, hfg
    common /mame/ iname, iprod
    
    ! Arrays
    real :: xm(50), th(50), rh(51), t(51,2), h(51,2), width(11), xlong(51)
    real :: pxm(11,51), pth(11,51), prh(11,51), pt(11,51), ph(11,51)
    real :: ptm(51), pkcon(51), pkab(51), pen(51), ph2o(51), pavnc(51)
    real :: pbtuh20(51), pxm1(51)
    
    ! Local variables
    real :: rhc, prl, yl, xmend, bph, yleng, xwide, delx, dbtpr
    real :: nlfx_real  ! Read as real, convert to integer
    integer :: iterct, iexit, kcon, nlfx, ind, ind1, indpx, indpy
    integer :: i, j, jm, ip1, krow, k, indpry, nnodes
    real :: thin, tin, hin, rhin, ga, hc, xme, gvel, gp, afg
    real :: con1, con2, con3, con4, con5, con6, con7
    real :: dely, scon1, scon2, scon3, tmth, ht, tabs, twba, hs
    real :: sum, xmave
    
    ! Initialize
    rhc = 0.9999999999
    prl = 0.0
    yl = 0.0
    iterct = 0
    iexit = 0
    kcon = 0
    kab = 0
    krow = 0
    
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
    
    ! Open files
    write(*,*) 'Opening CROSSFLOW.DAT...'
    open(unit=5, file='CROSSFLOW.DAT', status='old', action='read', err=999)
    open(unit=6, file='CROSSFLOW.OUT', status='replace', action='write')
    
    ! Input conditions
    write(*,*) 'Reading input parameters...'
    read(5, *) xmo, thin, tin, hin, cfm, bph
    read(5, *) yleng, xwide
    read(5, *) nlfx_real
    read(5, *) xmend
    
    ! Convert to integer
    nlfx = int(nlfx_real)
    
    write(*,*) 'Input read successfully:'
    write(*,*) '  XMO    =', xmo
    write(*,*) '  TIN    =', tin
    write(*,*) '  YLENG  =', yleng
    write(*,*) '  XWIDE  =', xwide
    write(*,*) '  NLFX   =', nlfx
    
    ! Compute step size and number of nodes
    delx = 1.0 / real(nlfx)
    ind = int(nlfx * xwide)
    ind1 = ind + 1
    indpx = max(1, ind1 / 10)
    indpy = int(yleng / xwide * 10.0) + 1
    dbtpr = real(indpx) * delx
    
    write(*,*) 'Grid created:'
    write(*,*) '  Nodes in width =', ind
    write(*,*) '  DELX =', delx
    
    ! Compute output widths for printing
    do i = 1, 11
        width(i) = real(i-1) * dbtpr
    end do
    
    ! Compute inlet RH and initialize arrays
    rhin = rhdbha(f_temp(tin), hin)
    
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
    
    ! Convert airflow to lb/hr
    ga = 60.0 * cfm / vsdbha(f_temp(thin), hin)
    
    if (ga >= 500.0) then
        hc = 0.363 * ga**0.59
    else
        hc = 0.69 * ga**0.49
    end if
    
    xme = emc(rhin, tin)
    
    ! Convert grain flow to ft/hr and lb/hr
    gvel = bph * 1.244
    gp = gvel * rhop
    afg = ga / gp
    
    write(*,*) 'Computed properties:'
    write(*,*) '  GA    =', ga, ' lb/hr'
    write(*,*) '  HC    =', hc, ' BTU/hr-ft2-F'
    write(*,*) '  GVEL  =', gvel, ' ft/hr'
    
    ! Print header
    write(6, 210) iname, iprod, tin, thin, rhin, hin, xmo, xme, afg, &
                  cfm, bph, ga, gp, ca, cp, cv, cw, hc, patm, hfg, &
                  rhop, sa, yleng, xwide, delx, xmend
    
    ! Compute constants
    con1 = 2.0 * ga * ca
    con2 = 2.0 * ga * cv
    con3 = hc * sa * delx
    con4 = gp * cp
    con5 = gp * cw
    con6 = 2.0 * con3
    con7 = ga * (ca + cv * hin) * (tin - thin)
    
    write(*,*) 'Starting length loop...'
    
    !===================================================================
    ! BEGIN LENGTH LOOP
    !===================================================================
    do while (iexit == 0)
        
        ! Compute size of this Y-step
        dely = 2.0 * delx * (con4 + con5 * xm(1)) / &
               (con1 + con2 * h(ind1,1)) * 0.9
        delt = dely / gvel
        
        ! Increment length
        yl = yl + dely
        scon1 = ga * dely / (gvel * delx)
        scon2 = rhop / scon1
        scon3 = hc * sa * dely / gvel
        
        !---------------------------------------------------------------
        ! BEGIN WIDTH LOOP
        !---------------------------------------------------------------
        do j = 2, ind1
            jm = j - 1
            tht = (th(jm) + t(jm,2)) / 2.0
            xmt = xm(jm)
            
            ! Skip theta equation on first length step
            if (iterct > 0) then
                if (xmt < 0.17) then
                    hfg = (1094.0 - 0.57 * tht) * &
                          (1.0 + 4.349 * exp(-28.25 * xmt))
                end if
                
                tmth = (t(jm,1) + t(j,1)) / 2.0 - th(jm)
                
                ! Theta equation
                th(jm) = th(jm) + (scon3 * tmth - &
                         (hfg + cv * tmth) * scon1 * (h(j,1) - h(jm,1))) / &
                         (con4 + con5 * xmt)
                
                tht = (th(jm) + t(jm,2)) / 2.0
            else
                tht = (t(jm,2) + 2.0 * t(jm,1) + t(j,1)) / 4.0
            end if
            
            ht = ((th(jm) + h(j,1)) / 2.0 + h(jm,2)) / 2.0
            rht = rhdbha(f_temp(tht), ht)
            
            ! Call layer subroutine
            call layer()
            
            hfg = 1000.0
            
            ! H equation
            h(j,2) = h(jm,2) - scon2 * (xmt - xm(jm))
            ht = (h(jm,2) + h(j,2)) / 2.0
            
            ! T equation
            t(j,2) = (t(jm,2) * (con1 + con2 * ht - con3) + th(jm) * con6) / &
                     (con1 + con2 * ht + con3)
            tabs = f_temp(t(j,2))
            
            ! Check for condensation
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
            
        end do  ! End width loop
        
        sum = 0.0
        
        ! Shift arrays and compute average moisture content
        do j = 2, ind1
            t(j,1) = t(j,2)
            h(j,1) = h(j,2)
            sum = sum + xm(j-1)
        end do
        
        xmave = sum / real(ind)
        iterct = iterct + 1
        
        ! Check if time to print or end
        if ((yl + dely) >= yleng .or. xmave <= xmend .or. yl >= prl) then
            
            ! Store values for printing
            prl = prl + dbtpr
            krow = krow + 1
            xlong(krow) = yl
            
            k = 0
            do j = 1, ind1, indpx
                jm = max(1, j-1)
                k = k + 1
                if (k <= 11) then
                    pxm(k,krow) = xm(jm)
                    pth(k,krow) = th(jm)
                    pt(k,krow) = t(j,1)
                    ph(k,krow) = h(j,1)
                    prh(k,krow) = rh(j)
                end if
            end do
            
            nnodes = ind1 * (iterct + 1)
            ptm(krow) = yl / gvel
            pxm1(krow) = xm(1)
            pkcon(krow) = real(kcon) * 100.0 / real(nnodes)
            pkab(krow) = real(kab) * 100.0 / real(nnodes)
            pen(krow) = con7 * ptm(krow)
            pavnc(krow) = xmave
            ph2o(krow) = (xmo - pavnc(krow)) * rhop * xwide
            if (ph2o(krow) > 0.0) then
                pbtuh20(krow) = pen(krow) / ph2o(krow)
            else
                pbtuh20(krow) = 0.0
            end if
            
            write(*,'(a,f8.2,a,f8.4)') '  Length =', yl, '  Avg MC =', xmave
        end if
        
        ! Check exit conditions
        if ((yl + dely) >= yleng) then
            iexit = 1
        else if (xmave <= xmend) then
            iexit = 1
            indpry = krow
        end if
        
    end do  ! End length loop
    
    ! Print results
    if (xmave >= xmend) indpry = krow
    
    write(6, 211)
    write(6, 217) (width(i), i = 1, 11)
    do j = 1, indpry
        write(6, 216) xlong(j), (pxm(i,j), i = 1, 11)
    end do
    
    write(6, 212)
    write(6, 217) (width(i), i = 1, 11)
    do j = 1, indpry
        write(6, 216) xlong(j), (pth(i,j), i = 1, 11)
    end do
    
    write(6, 213)
    write(6, 217) (width(i), i = 1, 11)
    do j = 1, indpry
        write(6, 216) xlong(j), (pt(i,j), i = 1, 11)
    end do
    
    write(6, 214)
    write(6, 217) (width(i), i = 1, 11)
    do j = 1, indpry
        write(6, 216) xlong(j), (ph(i,j), i = 1, 11)
    end do
    
    write(6, 215)
    write(6, 217) (width(i), i = 1, 11)
    do j = 1, indpry
        write(6, 216) xlong(j), (prh(i,j), i = 1, 11)
    end do
    
    write(6, 218)
    do j = 1, indpry
        write(6, 219) xlong(j), ptm(j), pavnc(j), pen(j), ph2o(j), &
                      pbtuh20(j), pkcon(j), pkab(j)
    end do
    
    close(5)
    close(6)
    
    write(*,*) ''
    write(*,*) 'Simulation complete!'
    write(*,*) 'Results written to CROSSFLOW.OUT'
    write(*,*) 'Final average MC =', xmave
    write(*,*) 'Total length =', yl, ' feet'
    
    stop
    
999 write(*,*) 'ERROR: Cannot open CROSSFLOW.DAT'
    stop
    
    !===================================================================
    ! FORMAT STATEMENTS
    !===================================================================
210 format(1h1, 43x, 'M I C H I G A N  S T A T E  U N I V E R S I T Y', &
           /33x, 'A G R I C U L T U R A L  E N G I N E E R I N G  D E P A R T M E N T', &
           /42x, 'C R O S S F L O W  D R Y E R  M O D E L', /59x, 'U S I N G  T H E', &
           /44x, a10, ' THINLAYER EQUATION FOR', a10, 10(/), &
           52x, 'INPUT PROPERTIES AND CONDITIONS', 5(/), &
           '  AIR TEMP(DEG F)  PROD TEMP(DEG F)   REL HUM(DECIMAL)    ABS HUM(LB/LB)', &
           '   DB MC(DECIMAL) EQUIL MC(DECIMAL) AIR/GRAIN RATIO', &
           /1x, 7(5x, f9.4, 5x), /20x, 'AIRFLOW', 10x, 'GRAIN FLOW', &
           /20x, f10.4, ' CFM', 6x, f10.4, ' BU/HR', &
           /20x, f10.4, ' LB/HR', 4x, f10.4, ' LB/HR', &
           4(/), 11x, 'HEAT CAPACITIES(BTU/LB)', 14x, 'AIR', 14x, 'PRODUCT', 10x, &
           'WATER VAPOR', 8x, 'WATER LIQUID', /34x, 4(13x, f6.4), 5(/), &
           24x, 'H T COEF CONV', 7x, 'ATMOS PRESS', 6x, 'LAT HEAT EVAP', 4x, &
           'BULK DENS DRY PROD', 3x, 'SPEC SURF AREA', /14x, 5(10x, f9.4), 10(/), &
           60x, 'PROGRAM CONTROLS', 5(/), &
           25x, 'SIMULATE A DRYER OF LENGTH', f5.2, ' FT AND WIDTH', f5.2, &
           ' FT USING INCREMENTS OF', f6.4, ' FT', &
           /25x, 'OR UNTIL THE MC FALLS BELOW', f8.6)
211 format(1h1, 55x, 'MOISTURE DISTRIBUTION')
212 format(1h1, 57x, 'PRODUCT TEMPERATURES')
213 format(1h1, 59x, 'AIR TEMPERATURES')
214 format(1h1, 57x, 'HUMIDITY DISTRIBUTION')
215 format(1h1, 58x, 'RELATIVE HUMIDITY')
216 format(1x, f10.3, 11f10.4)
217 format(///46x, 'WIDTH'/5x, 'DEPTH', 11(7x, f5.2))
218 format(1h1, 23x, 'EQUIVALENT', 7x, 'AVERAGE', 10x, 'ENERGY', 10x, 'WATER', &
           10x, 'BTU PER', 12x, 'CONDENSATION', 8x, 'ABSORPTION', &
           /1x, 'DEPTH', 14x, 'TIME', 5x, 'MOISTURE CONTENT', 5x, 'INPUT', &
           7x, 'REMOVED', 2x, 'LB H2O', 1x, 8x, 'OCCURRED', 8x, 'OCCURRED'/)
219 format(1x, f6.2, 9x, f7.4, 10x, f6.4, 9x, f8.2, 8x, f7.3, 9x, f8.2, &
           9x, f6.2, 10x, f6.2)
    
contains

    real function f_temp(t)
        real, intent(in) :: t
        f_temp = t + 459.69
    end function f_temp

end program crossflow_dryer


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
    ! Using simplified correlation
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
    
    ! Grain velocity (for crossflow - moving downward)
    ! Use actual grain velocity from common block calculation
    gvel = 0.1  ! Approximate - should be calculated from BPH
    
    ! dM/dt equation (Thompson)
    if (rad > 0.0) then
        xmt = xmt - (xmo - xme) / gvel * exp((-a - rad) / (b * b)) / rad * delt
    end if
    
    ! Prevent MC from going below equilibrium or negative
    if (xmt < xme) xmt = xme
    if (xmt < 0.0) xmt = 0.0
    
end subroutine layer
