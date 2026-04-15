program concurrent_dryer
    !-------------------------------------------------------------------
    ! CONCURRENT FLOW GRAIN DRYER MODEL
    !
    ! Michigan State University
    ! Agricultural Engineering Department
    ! F.W. Bakker-Arkema, Project Leader
    !
    ! Description:
    !   Simulation of a concurrent flow dryer where air and grain
    !   flow in the SAME direction (both downward)
    !-------------------------------------------------------------------
    !  use sychart_package
	use PsyFun
    !  use emc_corn
	use emc
    !  use rkamsub_modern
	use rkamsub
    implicit none
    
    ! Common blocks
    real :: xmo, cfm, gvel
    real :: xleng, tin, hin, thin
    real :: con1, con2, con3, con4, con5, con6, ga
    real :: sa, ca, cp, cv, cw, rhop, hfg
    character(len=10) :: iname, iprod
    real :: y(202)
    
    common /main/ xmo, cfm, gvel
    common /func/ xleng, tin, hin, thin
    common /constnt/ con1, con2, con3, con4, con5, con6, ga
    common /prprty/ sa, ca, cp, cv, cw, rhop, hfg
    common /mame/ iname, iprod
    common y
    
    ! Local variables
    real :: rhin, hc, xme, bph, gp, afgf
    real :: rh, etime, water, energy, btuh20, dbtpr, con7
    real :: prl
    integer :: iexit
    
    ! Initialize
    iexit = 0
    prl = 0.0
    
    ! Initialize properties
    sa = 239.0
    ca = 0.242
    cp = 0.268
    cv = 0.45
    cw = 1.0
    rhop = 38.71
    hfg = 1000.0
    patm = 14.30
    
    iname = 'THOMPSON  '
    iprod = ' CORN     '
    
    ! Open files
    write(*,*) 'CONCURRENT FLOW DRYER - Opening CONCURRENT.DAT...'
    open(unit=5, file='CONCURRENT.DAT', status='old', action='read', err=999)
    open(unit=6, file='CONCURRENT.OUT', status='replace', action='write')
    
    write(*,*) 'Reading input parameters...'
    read(5, *) xmo, thin, tin, hin, cfm, bph
    read(5, *) xleng, dbtpr
    
    write(*,*) 'Input read:'
    write(*,*) '  XMO   =', xmo
    write(*,*) '  TIN   =', tin
    write(*,*) '  XLENG =', xleng
    
    ! Calculate inlet RH
    rhin = rhdbha(f_temp(tin), hin)
    
    ! Convert airflow
    ga = 60.0 * cfm / vsdbha(f_temp(thin), hin)
    if (tin < thin) ga = 60.0 * cfm / vsdbha(f_temp(tin), hin)
    
    if (ga >= 500.0) then
        hc = 0.363 * ga**0.59
    else
        hc = 0.69 * ga**0.49
    end if
    
    xme = emc(rhin, tin)
    
    ! Convert grain flow
    gvel = bph * 1.244
    gp = gvel * rhop
    afgf = ga / gp
    
    write(*,*) 'Computed properties:'
    write(*,*) '  GA    =', ga
    write(*,*) '  HC    =', hc
    
    ! Print header
    write(6, 210) iname, iprod, tin, thin, rhin, hin, xmo, xme, afgf, cfm, bph, &
                  ga, gp, ca, cp, cv, cw, hc, patm, hfg, rhop, sa, xleng, dbtpr
    
    ! Compute constants
    con1 = ga * ca
    con2 = ga * cv
    con3 = hc * sa
    con4 = gp * cp
    con5 = gp * cw
    con6 = 1.0 / afgf
    con7 = ga * (ca + cv * hin) * (tin - thin)
    
    write(*,*) 'Starting simulation (concurrent flow - same direction)...'
    
    ! Print headings
    write(6, 211)
    
    ! Initialize Y array
    ! For concurrent: both air and grain enter at same end
    y(1) = tin        ! Air temperature (both start hot)
    y(2) = xmo        ! Moisture content
    y(3) = hin        ! Humidity ratio
    y(4) = thin       ! Product temperature
    y(5) = 0.0        ! Position
    y(11) = 0.0       ! Error flag
    
    rh = rhdbha(f_temp(y(1)), y(3))
    write(6, 212) y(5), 0.0, y(1), y(3), rh, y(4), y(2), 0.0
    
    ! Initialize RK integrator
    call start(4, 3, 1, 1.0e-3, 1.0e-6, 1.0e-8, 0.01, 1.0e-6, 0.5)
    
    write(*,*) 'Starting integration...'
    
    ! Main loop
    do while (iexit == 0)
        ! Update HFG if needed
        if (y(2) < 0.17) then
            hfg = (1094.0 - 0.57 * y(4)) * (1.0 + 4.349 * exp(-28.25 * y(2)))
        end if
        
        ! Take RK step
        call rkamsub()
        
        ! Compute RH
        rh = rhdbha(f_temp(y(1)), y(3))
        
        ! Check exit conditions
        if (y(11) > 1.0 .or. y(5) >= xleng) then
            iexit = 1
        end if
        
        ! Print if needed
        if (y(5) >= prl .or. iexit == 1) then
            prl = prl + dbtpr
            etime = y(5) / gvel
            water = (xmo - y(2)) * rhop * y(5)
            write(6, 212) y(5), etime, y(1), y(3), rh, y(4), y(2), water
            write(*,'(a,f8.2,a,f8.4)') '  Position =', y(5), '  MC =', y(2)
        end if
    end do
    
    ! Final output
    etime = y(5) / gvel
    water = (xmo - y(2)) * rhop * y(5)
    if (water > 0.0) then
        energy = con7 * etime
        btuh20 = energy / water
    else
        energy = 0.0
        btuh20 = 0.0
    end if
    
    write(6, 214) energy, water, btuh20
    
    close(5)
    close(6)
    
    write(*,*) ''
    write(*,*) 'Simulation complete!'
    write(*,*) 'Results in CONCURRENT.OUT'
    write(*,*) 'Final MC =', y(2)
    
    stop
    
999 write(*,*) 'ERROR: Cannot open CONCURRENT.DAT'
    stop
    
210 format(1h1, 43x, 'M I C H I G A N  S T A T E  U N I V E R S I T Y', &
           /33x, 'A G R I C U L T U R A L  E N G I N E E R I N G  D E P A R T M E N T', &
           /40x, 'C O N C U R R E N T  F L O W  D R Y E R  M O D E L', /59x, 'U S I N G  T H E', &
           /44x, a10, ' THINLAYER EQUATION FOR', a10, 10(/), &
           52x, 'INPUT PROPERTIES AND CONDITIONS', 5(/), &
           '  AIR TEMP(DEG F)  PROD TEMP(DEG F)   REL HUM(DECIMAL)    ABS HUM(LB/LB)', &
           '   DB MC(DECIMAL) EQUIL MC(DECIMAL) AIR/GRAIN RATIO', &
           /1x, 7(5x, f9.4, 5x), ///55x, 'AIRFLOW', 10x, 'GRAIN FLOW', &
           //53x, f10.4, ' CFM', 6x, f10.4, ' BU/HR', /53x, f10.4, ' LB/HR', 4x, f10.4, ' LB/HR', &
           4(/), 11x, 'HEAT CAPACITIES(BTU/LB)', 14x, 'AIR', 14x, 'PRODUCT', 10x, &
           'WATER VAPOR', 8x, 'WATER LIQUID', /34x, 4(13x, f6.4), 5(/), &
           24x, 'H T COEF CONV', 7x, 'ATMOS PRESS', 6x, 'LAT HEAT EVAP', 4x, &
           'BULK DENS DRY PROD', 3x, 'SPEC SURF AREA', /14x, 5(10x, f9.4), 10(/), &
           60x, 'PROGRAM CONTROLS', 5(/), 25x, 'SIMULATE A DRYER OF LENGTH', f6.2, &
           ' FT PRINTING EVERY', f5.2, ' FT')
211 format(1h1, 15x, 'DEPTH', 6x, 'TIME', 3x, 'AIR TEMP', 3x, 'ABS HUM', 3x, &
           'REL HUM', 2x, 'PROD TEMP', 3x, 'MC DB', 4x, 'WATER'/)
212 format(1h0, 10x, 3f10.2, 2f10.4, f10.2, 2f10.4)
214 format(///10x, 'TOTAL ENERGY INPUT =', f8.2, /10x, 'TOTAL WATER REMOVED =', &
           f7.4, /10x, 'BTU/LB H2O =', f8.2)
    
contains

    real function f_temp(t)
        real, intent(in) :: t
        f_temp = t + 459.69
    end function f_temp

end program concurrent_dryer


!-----------------------------------------------------------------------
! DERFUN - Derivative function for CONCURRENT flow
!-----------------------------------------------------------------------
subroutine derfun()
    ! use sychart_packageun
	use PsyFun
    !  use emc_corn
	use emc
    implicit none
    
    real :: xmo, cfm, gvel
    real :: xleng, tin, hin, thin
    real :: con1, con2, con3, con4, con5, con6, ga
    real :: sa, ca, cp, cv, cw, rhop, hfg
    real :: y(202)
    
    common /main/ xmo, cfm, gvel
    common /func/ xleng, tin, hin, thin
    common /constnt/ con1, con2, con3, con4, con5, con6, ga
    common /prprty/ sa, ca, cp, cv, cw, rhop, hfg
    common y
    
    real :: thin_loc, dmdt
    
    ! For CONCURRENT flow: air and grain move together
    ! Air temperature derivative (air cools as it loses heat to grain)
    thin_loc = y(1) - y(4)
    y(6) = -con3 / (con1 + con2 * y(3)) * thin_loc
    
    ! Moisture derivative from thin-layer equation
    call difeq(dmdt)
    y(7) = dmdt
    
    ! Humidity derivative (air picks up moisture)
    y(8) = -con6 * dmdt
    
    ! Product temperature derivative
    y(9) = (con3 * thin_loc - (hfg + cv * thin_loc) * ga * y(8)) / &
           (con4 + con5 * y(2))
    
    ! Position derivative
    y(10) = 1.0
    
end subroutine derfun


!-----------------------------------------------------------------------
! DIFEQ - Thompson's equation
!-----------------------------------------------------------------------
subroutine difeq(dmdt)
    ! use emc_corn
	use emc
    !  use sychart_package
	use PsnFun
    implicit none
    real, intent(out) :: dmdt
    
    real :: xmo, cfm, gvel
    real :: y(202)
    
    common /main/ xmo, cfm, gvel
    common y
    
    real :: a, b, xme, xmr, almr, ti, rad, rht, t_abs
    
    ! Thompson parameters
    a = -1.86178 + 0.0048843 * y(4)
    b = 427.364 * exp(-0.03301 * y(4))
    
    ! EMC
    t_abs = y(4) + 459.69
    rht = rhdbha(t_abs, y(3))
    
    if (rht >= 1.0) then
        xme = y(2)
    else if (rht < 0.01) then
        xme = 0.05
    else
        xme = 0.05 + 0.20 * rht
        if (xme > y(2)) xme = y(2)
    end if
    
    ! Moisture ratio
    if (xmo > xme) then
        xmr = (y(2) - xme) / (xmo - xme)
    else
        xmr = 0.01
    end if
    
    if (xmr <= 0.0) then
        xmr = 0.01
        y(11) = 2.0
    end if
    
    almr = log(xmr)
    ti = almr * (a + b * almr)
    rad = sqrt(abs(a * a + 4.0 * b * ti))
    
    if (rad > 0.0) then
        dmdt = -(xmo - xme) / gvel * exp((-a - rad) / (b * b)) / rad
    else
        dmdt = 0.0
    end if
    
    if (y(2) < xme) dmdt = 0.0
    
end subroutine difeq
