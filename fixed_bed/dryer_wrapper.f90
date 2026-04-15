subroutine run_dryer_simulation(user_name, project_name, address, crop_name, &
                                 simulation_date, xmo, thin, tin, hin, cfm, &
                                 depth, indpr_real, nlpf_real, tt, tbtpr, xmend, &
                                 sa, ca, cp, cv, rhop, hfg, &
                                 moisture_out, temp_out, time_out, n_points, &
                                 final_moisture, drying_time, success)
    !-------------------------------------------------------------------
    ! Python-callable wrapper for dryer simulation
    ! No file I/O - all data passed as parameters
    !-------------------------------------------------------------------
    use PsyFun
    use emc_grain
    implicit none
    
    ! Input parameters - metadata
    character(len=100), intent(in) :: user_name
    character(len=100), intent(in) :: project_name
    character(len=200), intent(in) :: address
    character(len=50), intent(in) :: crop_name
    character(len=50), intent(in) :: simulation_date
    
    ! Input parameters - process conditions
    real, intent(in) :: xmo        ! Initial moisture (%)
    real, intent(in) :: thin       ! Initial grain temp (C)
    real, intent(in) :: tin        ! Air temperature (C)
    real, intent(in) :: hin        ! Relative humidity (%)
    real, intent(in) :: cfm        ! Air flow rate (CFM)
    real, intent(in) :: depth      ! Bed depth (m)
    real, intent(in) :: indpr_real ! Print interval
    real, intent(in) :: nlpf_real  ! Number of layers
    real, intent(in) :: tt         ! Time step
    real, intent(in) :: tbtpr      ! Output interval
    real, intent(in) :: xmend      ! Target moisture (%)
    
    ! Input parameters - crop properties
    real, intent(in) :: sa         ! Specific surface area
    real, intent(in) :: ca         ! Heat capacity air
    real, intent(in) :: cp         ! Heat capacity product
    real, intent(in) :: cv         ! Heat capacity vapor
    real, intent(in) :: rhop       ! Dry bulk density
    real, intent(in) :: hfg        ! Latent heat
    
    ! Output arrays
    integer, parameter :: MAX_POINTS = 1000
    real, dimension(MAX_POINTS), intent(out) :: moisture_out
    real, dimension(MAX_POINTS), intent(out) :: temp_out
    real, dimension(MAX_POINTS), intent(out) :: time_out
    integer, intent(out) :: n_points
    
    ! Output summary
    real, intent(out) :: final_moisture
    real, intent(out) :: drying_time
    integer, intent(out) :: success  ! 1=success, 0=failed
    
    ! Local variables (same as original program)
    real :: xmt, tht, rht, delt
    integer :: kab
    real :: cw
    character(len=10) :: iname, iprod
    
    real :: xm(150), th(150), rh(151), t(151,2), h(151,2), deep(20)
    real :: rhc, d, prt, time
    integer :: iterct, iexit, jk, kcon
    real :: delx, dbtpr, rhin, ga, hc, xme
    real :: con1, con2, con3, con4, con5, con6, con7
    real :: scon1, scon2, scon3, tmth, ht, tabs, twba, hs, sum, xmave
    real :: pkcon, pkab, energy, water, btuh20
    integer :: indpr, nlpf, ind, indi, i, ip1, j, jm, jr, nodes
    
    ! Initialize
    success = 0
    n_points = 0
    
    write(*,*) '========================================='
    write(*,*) 'FORTRAN SIMULATION STARTING'
    write(*,*) 'User:', trim(user_name)
    write(*,*) 'Crop:', trim(crop_name)
    write(*,*) 'Initial MC:', xmo, '%'
    write(*,*) 'Target MC:', xmend, '%'
    write(*,*) '========================================='
    
    ! Set constants
    cw = 1.0
    iname = 'PYTHON    '
    iprod = trim(crop_name)
    
    ! Convert real to integer
    indpr = int(indpr_real)
    nlpf = int(nlpf_real)
    
    ! Initialize arrays and variables
    rhc = 0.9999999999
    d = 0.0
    prt = 0.0
    time = 0.0
    iterct = 0
    iexit = 0
    jk = 0
    kcon = 0
    kab = 0
    
    ! Compute step size, number of nodes
    delx = 1.0 / real(nlpf)
    nodes = nlpf + 1
    dbtpr = depth / real(jk)
    
    ! Set print depths
    do i = 1, jk
        deep(i) = dbtpr * real(i)
    end do
    
    ! Calculate psychrometric properties
    rhin = rhdbha(f_temp(tin), hin)
    ga = 60.0 * cfm / vsdbha(f_temp(thin), hin)
    hc = 0.89 * (ga / 60.0)**0.67
    xme = emc(rhin, tin)
    
    ! Initialize profiles
    do i = 1, nodes
        xm(i) = xmo
        th(i) = thin
        h(i,1) = hin
        h(i,2) = hin
        t(i,1) = tin
        t(i,2) = tin
    end do
    
    rh(1) = rhin
    
    ! Compute constants
    con1 = 2.0 * ga * ca
    con2 = 2.0 * ga * cv
    con3 = hc * sa * delx
    con4 = rhop * cp
    con5 = rhop * cw
    con6 = 2.0 * con3
    con7 = ga * (ca + cv * hin) * (tin - thin)
    
    ! Main simulation loop
    do while (iexit == 0)
        
        ! Compute time step
        delt = 2.0 * delx * (con4 + con5 * xm(1)) / &
               (con1 + con2 * h(1,2) + con6)
        
        if (delt > tt) delt = tt
        
        time = time + delt
        
        ! Update moisture and temperature profiles
        ! [Insert main calculation logic here - simplified for example]
        
        ! Calculate average moisture
        xmave = 0.0
        do i = 1, nodes
            xmave = xmave + xm(i)
        end do
        xmave = xmave / real(nodes)
        
        ! Store output points
        if (n_points < MAX_POINTS) then
            n_points = n_points + 1
            time_out(n_points) = time
            moisture_out(n_points) = xmave
            temp_out(n_points) = th(1)
        end if
        
        ! Check exit conditions
        if (xmave <= xmend .or. time > 24.0) then
            iexit = 1
        end if
        
        iterct = iterct + 1
        if (iterct > 100000) then
            write(*,*) 'WARNING: Max iterations reached'
            iexit = 1
        end if
        
    end do
    
    ! Set output summary
    final_moisture = xmave
    drying_time = time
    success = 1
    
    write(*,*) '========================================='
    write(*,*) 'SIMULATION COMPLETE'
    write(*,*) 'Final MC:', final_moisture, '%'
    write(*,*) 'Time:', drying_time, 'hours'
    write(*,*) 'Data points:', n_points
    write(*,*) '========================================='
    
contains

    real function f_temp(t)
        real, intent(in) :: t
        f_temp = t + 459.69
    end function f_temp

end subroutine run_dryer_simulation
