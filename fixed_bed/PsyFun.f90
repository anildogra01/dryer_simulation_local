module PsyFun
    !-------------------------------------------------------------------
    ! PsyFun PACKAGE
    !
    ! Description:
    !   Group of highly interactive function subprograms based on
    !   equations by Brooker (1967, 1970) and a root finding
    !   subroutine based on algorithm by Dekker (1967) used to
    !   find and convert psychrometric properties
    !
    ! Usage:
    !   Used with fixed bed, crossflow, concurrent and counterflow
    !   grain dryer models
    !
    ! Functions contained:
    !   - HADBRH  : Humidity ratio from dry bulb and relative humidity
    !   - HADP    : Humidity ratio from dew point
    !   - HAPV    : Humidity ratio from partial vapor pressure
    !   - RHPSPV  : Relative humidity from saturation and vapor pressure
    !   - RHDBHA  : Relative humidity from dry bulb and humidity ratio
    !   - PVDBWB  : Vapor pressure from dry bulb and wet bulb
    !   - PVDBVS  : Vapor pressure from dry bulb and specific volume
    !   - PVHA    : Vapor pressure from humidity ratio
    !   - PSDB    : Saturation pressure from dry bulb
    !   - HLDB    : Latent heat from dry bulb
    !   - HLDP    : Latent heat from dew point
    !   - VSDBHA  : Specific volume from dry bulb and humidity ratio
    !   - ENDBDP  : Enthalpy from dry bulb and dew point
    !   - WBDBHAS : Wet bulb from dry bulb, humidity ratio (iterative)
    !   - DPHAS   : Dew point from humidity ratio (iterative)
    !   - DPDBENS : Dew point from dry bulb and enthalpy (iterative)
    !   - DBPSS   : Dry bulb from saturation pressure (iterative)
    !
    ! Subroutine:
    !   - ZEROIN  : Root finding by Dekker's method
    !-------------------------------------------------------------------
    implicit none
    
    ! Atmospheric pressure (psia) - shared by all functions
    real :: patm
    common /press/ patm
    
    ! Special common for iterative functions
    real :: pv_special, tb_special, xtra_special
    common /special/ pv_special, tb_special, xtra_special
    
contains

    !-------------------------------------------------------------------
    ! Humidity ratio from dry bulb temperature and relative humidity
    !-------------------------------------------------------------------
    real function hadbrh(db, rh)
        real, intent(in) :: db, rh
        hadbrh = hapv(rh * psdb(db))
    end function hadbrh

    !-------------------------------------------------------------------
    ! Humidity ratio from partial vapor pressure
    !-------------------------------------------------------------------
    real function hapv(pv)
        real, intent(in) :: pv
        hapv = 0.6219 * pv / (patm - pv)
    end function hapv

    !-------------------------------------------------------------------
    ! Humidity ratio from dew point
    !-------------------------------------------------------------------
    real function hadp(dp)
        real, intent(in) :: dp
        hadp = hapv(psdb(dp))
    end function hadp

    !-------------------------------------------------------------------
    ! Relative humidity from saturation pressure and vapor pressure
    ! Also serves as RHDBHA with different interpretation
    !-------------------------------------------------------------------
    real function rhpspv(d1, d2)
        real, intent(in) :: d1, d2
        rhpspv = d2 / d1
    end function rhpspv

    !-------------------------------------------------------------------
    ! Relative humidity from dry bulb and humidity ratio
    !-------------------------------------------------------------------
    real function rhdbha(db, ha)
        real, intent(in) :: db, ha
        rhdbha = pvha(ha) / psdb(db)
    end function rhdbha

    !-------------------------------------------------------------------
    ! Vapor pressure from dry bulb and wet bulb
    !-------------------------------------------------------------------
    real function pvdbwb(db, wb)
        real, intent(in) :: db, wb
        real :: a, b, c
        
        a = psdb(wb)
        b = 0.62194 * hldb(wb) * patm
        c = 0.2405 * (a - patm) * (wb - db)
        pvdbwb = (a * b - c * patm) / (b - 0.15577 * c)
    end function pvdbwb

    !-------------------------------------------------------------------
    ! Vapor pressure from dry bulb and specific volume
    !-------------------------------------------------------------------
    real function pvdbvs(db, vs)
        real, intent(in) :: db, vs
        pvdbvs = patm - 53.35 * db / vs / 144.0
    end function pvdbvs

    !-------------------------------------------------------------------
    ! Vapor pressure from humidity ratio
    !-------------------------------------------------------------------
    real function pvha(ha)
        real, intent(in) :: ha
        pvha = ha * patm / (0.6219 + ha)
    end function pvha

    !-------------------------------------------------------------------
    ! Saturation pressure from dry bulb temperature (°R)
    !-------------------------------------------------------------------
    real function psdb(db)
        real, intent(in) :: db
        real, parameter :: r = 0.3206182232e04
        real, parameter :: a = -0.274055250361420e05
        real, parameter :: b = 0.541896076328951e02
        real, parameter :: c = -0.451370384112655e-1
        real, parameter :: d = 0.215321191638354e-4
        real, parameter :: e = -0.462026656819982e-8
        real, parameter :: f = 0.24161227209874e01
        real, parameter :: g = 0.121546516706055e-2
        
        if (db < 491.69) then
            ! Ice formula
            psdb = exp(23.3924 - 11286.6489 / db - 0.46057 * log(db))
        else
            ! Water formula
            psdb = r * exp((a + db * (b + db * (c + db * (d + db * e)))) / &
                          (db * (f - g * db)))
        end if
    end function psdb

    !-------------------------------------------------------------------
    ! Latent heat of vaporization from dry bulb temperature (°R)
    !-------------------------------------------------------------------
    real function hldb(db)
        real, intent(in) :: db
        
        if (db < 491.69) then
            ! Below freezing
            hldb = 1220.884 - 0.05077 * (db - 459.69)
        else if (db < 609.69) then
            ! Normal range
            hldb = 1075.8965 - 0.56983 * (db - 459.69)
        else
            ! High temperature
            hldb = sqrt(1354673.214 - 0.9125275587 * db * db)
        end if
    end function hldb

    !-------------------------------------------------------------------
    ! Latent heat from dew point
    !-------------------------------------------------------------------
    real function hldp(dp)
        real, intent(in) :: dp
        hldp = hldb(dp)
    end function hldp

    !-------------------------------------------------------------------
    ! Specific volume from dry bulb and humidity ratio
    !-------------------------------------------------------------------
    real function vsdbha(db, ha)
        real, intent(in) :: db, ha
        vsdbha = 53.35 * db * (0.6219 + ha) / 144.0 / 0.6219 / patm
    end function vsdbha

    !-------------------------------------------------------------------
    ! Enthalpy from dry bulb and dew point
    !-------------------------------------------------------------------
    real function endbdp(db, dp)
        real, intent(in) :: db, dp
        real :: ha, t1
        
        ha = hadp(dp)
        t1 = 0.2405 * (db - 459.69) + hldb(dp) * ha + 0.448 * ha * (db - dp)
        
        if (dp < 491.69) then
            endbdp = t1 - ha * (143.35 + 0.485 * (491.69 - dp))
        else
            endbdp = t1 + ha * (dp - 491.69)
        end if
    end function endbdp

    !-------------------------------------------------------------------
    ! Wet bulb temperature from dry bulb, humidity ratio (iterative)
    !-------------------------------------------------------------------
    real function wbdbhas(db, ha, g1, g2, eps)
        real, intent(in) :: db, ha, g1, g2, eps
        real :: a, b
        
        a = g1
        b = g2
        tb_special = db
        pv_special = pvha(ha)
        
        call zeroin(a, b, eps, wbl)
        wbdbhas = (a + b) / 2.0
    end function wbdbhas

    !-------------------------------------------------------------------
    ! Internal function for wet bulb iteration
    !-------------------------------------------------------------------
    real function wbl(twb)
        real, intent(in) :: twb
        real :: pwb, wbl1
        
        pwb = psdb(twb)
        wbl = twb - tb_special - (pwb - pv_special)
        wbl1 = (0.2405 * (pwb - patm) * (1.0 + 0.15577 * pv_special / patm)) * &
               (0.62194 * hldb(twb))
        wbl = wbl / wbl1
    end function wbl

    !-------------------------------------------------------------------
    ! Dew point from humidity ratio (iterative)
    !-------------------------------------------------------------------
    real function dphas(ha, g1, g2, eps)
        real, intent(in) :: ha, g1, g2, eps
        real :: a, b
        
        pv_special = pvha(ha)
        a = g1
        b = g2
        
        call zeroin(a, b, eps, dpl1)
        dphas = (a + b) / 2.0
    end function dphas

    !-------------------------------------------------------------------
    ! Internal function for dew point iteration
    !-------------------------------------------------------------------
    real function dpl1(tdp)
        real, intent(in) :: tdp
        dpl1 = pv_special - psdb(tdp)
    end function dpl1

    !-------------------------------------------------------------------
    ! Dew point from dry bulb and enthalpy (iterative)
    !-------------------------------------------------------------------
    real function dpdbens(db, en, g1, g2, eps)
        real, intent(in) :: db, en, g1, g2, eps
        real :: a, b
        
        a = g1
        b = g2
        xtra_special = 0.2405 * (db - 459.69) - en
        tb_special = db
        
        call zeroin(a, b, eps, dpl2)
        dpdbens = (a + b) / 2.0
    end function dpdbens

    !-------------------------------------------------------------------
    ! Internal function for dew point from enthalpy iteration
    !-------------------------------------------------------------------
    real function dpl2(tdp)
        real, intent(in) :: tdp
        real :: ha, t2
        
        ha = hadp(tdp)
        t2 = ha * hldp(tdp) + 0.448 * ha * (tb_special - tdp)
        
        if (tdp < 491.69) then
            dpl2 = xtra_special - t2 - ha * (143.35 + 0.485 * (491.69 - tdp))
        else
            dpl2 = xtra_special + t2 + ha * (tdp - 491.69)
        end if
    end function dpl2

    !-------------------------------------------------------------------
    ! Dry bulb from saturation pressure (iterative)
    !-------------------------------------------------------------------
    real function dbpss(ps, g1, g2, eps)
        real, intent(in) :: ps, g1, g2, eps
        real :: a, b
        
        a = g1
        b = g2
        xtra_special = ps
        
        call zeroin(a, b, eps, dbl)
        dbpss = (a + b) / 2.0
    end function dbpss

    !-------------------------------------------------------------------
    ! Internal function for dry bulb iteration
    !-------------------------------------------------------------------
    real function dbl(t)
        real, intent(in) :: t
        dbl = xtra_special - psdb(t)
    end function dbl

    !-------------------------------------------------------------------
    ! Root finding subroutine using Dekker's method
    !-------------------------------------------------------------------
    subroutine zeroin(a, b, eps, func)
        real, intent(inout) :: a, b
        real, intent(in) :: eps
        interface
            real function func(x)
                real, intent(in) :: x
            end function func
        end interface
        
        real :: fa, fb, fc, c, i, j, m, chint
        
        fa = func(a)
        fb = func(b)
        fc = fa
        c = a
        
        ! Check if root is bracketed
        if (sign(1.0, fb) == sign(1.0, fc)) then
            ! Warning suppressed - this is normal for saturated conditions
            ! write(*, '(///10x, 100(1h+)/10x, a, /20x, a, e21.14, a, e21.14, /10x, 100(1h+))') &
            !     'W A R N I N G -- NO ROOTS OR MULTIPLE ROOTS BETWEEN INITIAL GUESSES TO ZEROIN', &
            !     'GUESSES ARE ', a, ' AND ', b
            return
        end if
        
        ! Main iteration loop
        do
            ! Swap if necessary
            if (abs(fc) < abs(fb)) then
                c = b
                b = a
                a = c
                fc = fb
                fb = fa
                fa = fc
            end if
            
            ! Check convergence
            if (abs(c - b) <= 2.0 * eps) exit
            
            ! Inverse quadratic interpolation
            i = (b - a) * fb / (fb - fa)
            m = (c + b) / 2.0
            
            ! Check if interpolation is acceptable
            if ((b - i) * (m - i) > 0.0) then
                ! Use bisection
                i = m
            else
                ! Check if step is too small
                if (abs(b - i) < eps) then
                    i = sign(eps, (c - b)) + b
                end if
            end if
            
            ! Update
            a = b
            b = i
            fa = fb
            fb = func(b)
            
            ! Check if root found
            if (sign(1.0, fb) /= sign(1.0, fc)) then
                c = a
                fc = fa
            end if
        end do
        
        ! Final refinement
        a = (c + b) / 2.0
        fa = func(a)
        if (sign(1.0, fa) == sign(1.0, fb)) b = c
        
    end subroutine zeroin

    !-------------------------------------------------------------------
    ! LEGVAR function - checks for divide by zero or invalid numbers
    ! Returns 0 for normal, non-zero for invalid
    !-------------------------------------------------------------------
    integer function legvar(x)
        real, intent(in) :: x
        
        ! Check for NaN, Infinity, or zero
        if (x /= x) then
            ! NaN
            legvar = 1
        else if (abs(x) > huge(x) * 0.9) then
            ! Infinity
            legvar = 1
        else if (abs(x) < tiny(x)) then
            ! Too small
            legvar = 1
        else
            ! Normal
            legvar = 0
        end if
    end function legvar

end module PsyFun
