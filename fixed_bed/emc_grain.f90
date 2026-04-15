module emc_grain
    !-------------------------------------------------------------------
    ! Equilibrium Moisture Content for Corn
    !
    ! Programmer: G.F. DeBoer
    !
    ! Description:
    !   Function to compute equilibrium moisture content of corn from
    !   relative humidity and temperature.
    !
    ! Equations:
    !   - DeBoer equation for T < 235°F
    !   - T.L. Thompson equation for T >= 235°F
    !-------------------------------------------------------------------
    implicit none
    
contains

    !-------------------------------------------------------------------
    ! EMC - Equilibrium Moisture Content
    !-------------------------------------------------------------------
    real function emc(rh, t)
        !
        ! Arguments:
        !   rh  - Relative humidity (decimal, 0-1)
        !   t   - Temperature (°F)
        !
        ! Returns:
        !   EMC - Equilibrium moisture content (decimal, dry basis)
        !
        implicit none
        real, intent(in) :: rh, t
        
        ! Local variables
        real :: f0, f1, f2, f3, s1, s2, a, b
        
        ! Check temperature to determine which equation to use
        if (t < 235.0) then
            !-----------------------------------------------------------
            ! DeBoer Equation (T < 235°F)
            !-----------------------------------------------------------
            
            if (rh <= 0.5) then
                !-------------------------------------------------------
                ! Part 1: RH <= 0.5
                !-------------------------------------------------------
                
                ! Compute constants
                f1 = -0.0002922 * t + 0.1000
                f2 = -0.0004353 * t + 0.1328
                f3 = -0.0005359 * t + 0.1646
                s1 = 13.838 * (-9.0*f1 + 6.0*f2 - f3)
                s2 = 13.838 * (4.0*f3 - 9.0*f2 - 6.0*f1)
                b = rh - 0.17
                
                ! Find interval and compute EMC
                if (b <= 0.0) then
                    ! RH <= 0.17
                    emc = (s1 * rh**3 / 1.02 + (f1/0.17 - s1*0.02833) * rh)
                    
                else if (rh <= 0.34) then
                    ! 0.17 < RH <= 0.34
                    a = 0.34 - rh
                    emc = (s1 * a**3 / 1.02 + s2 * b**3 / 1.02 + &
                           (f2/0.17 - s2*0.02833) * b + &
                           (f1/0.17 - s1*0.02833) * a)
                    
                else
                    ! 0.34 < RH <= 0.5
                    a = 0.51 - rh
                    emc = (s2 * a**3 / 1.02 + (f3/0.17) * (rh - 0.34) + &
                           (f2/0.17 - s2*0.028333) * a)
                end if
                
            else
                !-------------------------------------------------------
                ! Part 2: RH > 0.5
                !-------------------------------------------------------
                
                ! Compute constants
                f0 = -0.0005373 * t + 0.1624
                f1 = -0.0007075 * t + 0.2075
                f2 = -0.0007449 * t + 0.2532
                f3 = -0.0001071 * t + 0.3931
                s1 = 13.838 * (4.0*f0 - 9.0*f1 + 6.0*f2 - f3)
                s2 = 13.838 * (4.0*f3 - 9.0*f2 + 6.0*f1 - f0)
                b = rh - 0.66
                
                ! Find interval and compute EMC
                if (b <= 0.0) then
                    ! 0.5 < RH <= 0.66
                    a = rh - 0.49
                    emc = (s1 * a**3 / 1.02 + (f1/0.17 - s1*0.02833) * a + &
                           (f0/0.17) * (0.66 - rh))
                    
                else if (rh <= 0.83) then
                    ! 0.66 < RH <= 0.83
                    a = 0.83 - rh
                    emc = (s1 * a**3 / 1.02 + s2 * b**3 / 1.02 + &
                           (f2/0.17 - s2*0.02833) * b + &
                           (f1/0.17 - s1*0.028333) * a)
                    
                else
                    ! 0.83 < RH <= 1.0
                    a = 1.0 - rh
                    emc = (s2 * a**3 / 1.02 + (f3/0.17) * (rh - 0.83) + &
                           (f2/0.17 - s2*0.02833308) * a)
                end if
            end if
            
        else
            !-----------------------------------------------------------
            ! Thompson Equation (T >= 235°F)
            !-----------------------------------------------------------
            
            ! Prevent log of zero or negative
            if (rh >= 0.9999) then
                emc = 0.50  ! Maximum reasonable EMC
            else
                emc = 0.01 * sqrt((-log(1.0 - rh)) / (0.0000382 * (t + 50.0)))
            end if
        end if
        
    end function emc

end module emc_grain
