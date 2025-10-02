import type { JSX } from 'react'
import Experiments from '../components/experiments/experiments.tsx'
import Analytics from '../components/analytics/analytics.tsx'
import ControllerConfigurator from '../components/configurator/controller/controller-configurator.tsx'
import ExperimentConfigurator from '../components/configurator/experiment/experiment-configurator.tsx'
import EnvironmentConfigurator from '../components/configurator/environment/environment-configurator.tsx'

export interface Route {
  path: string
  label: string
  component: JSX.Element
  description?: string
}

export const ROUTES: Route[] = [
  {
    path: '/',
    label: 'Experiments',
    description: 'Experiments dashboard',
    component: <Experiments />,
  },
  {
    path: '/data-analytics',
    label: 'Data Analytics',
    description: 'Analytics of experiment results',
    component: <Analytics />,
  },
  {
    path: '/environment-configurator',
    label: 'Environment',
    description: 'Configurator for environments',
    component: <EnvironmentConfigurator />,
  },
  {
    path: '/controller-configurator',
    label: 'Controller',
    description: 'Configurator for controllers',
    component: <ControllerConfigurator />,
  },
  {
    path: '/experiment-configurator',
    label: 'Experiments',
    description: 'Configurator for experiments',
    component: <ExperimentConfigurator />,
  },
]
