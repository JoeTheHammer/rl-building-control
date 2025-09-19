import {
  NavigationMenu,
  NavigationMenuContent,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
  NavigationMenuTrigger,
} from './ui/navigation-menu.tsx'
import { useLocation, Link } from 'react-router-dom'
import { ROUTES } from '../lib/routes.tsx'

const configuratorRoutes = ROUTES.filter((r) => r.path.includes('configurator'))

const NavigationBar = () => {
  const location = useLocation()
  const isActive = (path: string) => location.pathname === path

  const linkAndTriggerStyle =
    'group inline-flex h-10 w-full items-center justify-center px-4 py-2 text-lg font-medium transition-colors hover:bg-slate-100 hover:text-slate-900 focus:bg-slate-100 focus:outline-none disabled:pointer-events-none disabled:opacity-50 data-[active]:bg-slate-200 data-[active]:text-slate-900 data-[state=open]:bg-slate-100'

  return (
    <div className="flex justify-center p-2 shadow-md">
      <NavigationMenu className="w-full" viewport={false}>
        <NavigationMenuList className="w-full space-x-1 p-2">
          <NavigationMenuItem>
            <NavigationMenuLink asChild className={linkAndTriggerStyle}>
              <Link to="/" data-active={isActive('/') ? 'true' : undefined}>
                Experiments
              </Link>
            </NavigationMenuLink>
          </NavigationMenuItem>

          <NavigationMenuItem>
            <NavigationMenuLink asChild className={linkAndTriggerStyle}>
              <Link
                to="/data-analytics"
                data-active={isActive('/data-analytics') ? 'true' : undefined}
              >
                Data Analytics
              </Link>
            </NavigationMenuLink>
          </NavigationMenuItem>

          <NavigationMenuItem>
            <NavigationMenuTrigger className={linkAndTriggerStyle}>
              Configurators
            </NavigationMenuTrigger>
            <NavigationMenuContent className="min-w-[180px] border border-slate-200 bg-white shadow-xl">
              <ul className="flex flex-col gap-1 p-2">
                {configuratorRoutes.map((route) => (
                  <li key={route.path}>
                    <NavigationMenuLink
                      asChild
                      className="text-md block w-full rounded-lg px-4 py-2 font-medium text-slate-700 hover:bg-slate-100 hover:text-slate-900 focus:bg-slate-100 data-[active]:bg-slate-200"
                    >
                      <Link
                        to={route.path}
                        data-active={isActive(route.path) ? 'true' : undefined}
                      >
                        {route.label}
                      </Link>
                    </NavigationMenuLink>
                  </li>
                ))}
              </ul>
            </NavigationMenuContent>
          </NavigationMenuItem>
        </NavigationMenuList>
      </NavigationMenu>
    </div>
  )
}

export default NavigationBar
