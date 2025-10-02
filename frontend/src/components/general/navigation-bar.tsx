import {
  NavigationMenu,
  NavigationMenuContent,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
  NavigationMenuTrigger,
} from '../ui/navigation-menu.tsx'
import { useLocation, Link } from 'react-router-dom'
import { ROUTES } from '../../lib/routes.tsx'
import { FlaskConical, ChartNoAxesCombined, Settings } from 'lucide-react'

const configuratorRoutes = ROUTES.filter((r) => r.path.includes('configurator'))

const NavigationBar = () => {
  const location = useLocation()
  const isActive = (path: string) => location.pathname === path

  const linkAndTriggerStyle = `
    group inline-flex h-10 w-full items-center justify-center px-4 py-2 text-lg font-medium
    transition-colors duration-200 ease-in-out
    rounded-md
    text-foreground
    bg-transparent
    hover:bg-primary-hover
    hover:text-primary-foreground
    disabled:pointer-events-none
    disabled:opacity-50
    data-[active=true]:bg-primary
    data-[active=true]:text-primary-foreground
  `

  return (
    <div className="flex justify-center p-2 shadow-md">
      <NavigationMenu className="w-full" viewport={false}>
        <NavigationMenuList className="flex w-full space-x-1 p-2">
          {/* Experiments */}
          <NavigationMenuItem>
            <NavigationMenuLink
              asChild
              data-active={isActive('/') ? 'true' : undefined}
              className={`${linkAndTriggerStyle} flex items-center gap-2`}
            >
              <Link to="/">
                <FlaskConical className="size-4" />
                <span>Experiments</span>
              </Link>
            </NavigationMenuLink>
          </NavigationMenuItem>

          {/* Configurators Dropdown */}
          <NavigationMenuItem>
            <NavigationMenuTrigger
              data-active={
                configuratorRoutes.some((r) => isActive(r.path))
                  ? 'true'
                  : undefined
              }
              className={`${linkAndTriggerStyle} flex items-center gap-2`}
            >
              <Settings className="size-4" />
              <span>Configurators</span>
            </NavigationMenuTrigger>
            <NavigationMenuContent className="min-w-[180px] border border-slate-200 bg-white shadow-xl">
              <ul className="flex flex-col gap-1 p-2">
                {configuratorRoutes.map((route) => (
                  <li key={route.path}>
                    <NavigationMenuLink
                      asChild
                      data-active={isActive(route.path) ? 'true' : undefined}
                      className={linkAndTriggerStyle}
                    >
                      <Link to={route.path}>{route.label}</Link>
                    </NavigationMenuLink>
                  </li>
                ))}
              </ul>
            </NavigationMenuContent>
          </NavigationMenuItem>
          {/* Data Analytics */}
          <NavigationMenuItem>
            <NavigationMenuLink
              asChild
              data-active={isActive('/data-analytics') ? 'true' : undefined}
              className={`${linkAndTriggerStyle} flex items-center gap-2`}
            >
              <Link to="/data-analytics">
                <ChartNoAxesCombined className="size-4" />
                <span>Data Analytics</span>
              </Link>
            </NavigationMenuLink>
          </NavigationMenuItem>
        </NavigationMenuList>
      </NavigationMenu>
    </div>
  )
}

export default NavigationBar
