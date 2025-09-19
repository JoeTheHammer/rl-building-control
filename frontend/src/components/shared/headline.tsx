import React from 'react'

interface HeadlineProps {
  text: string
  className?: string
}

const Headline: React.FC<HeadlineProps> = ({ text, className }) => {
  return (
    <>
      <span
        className={`text-primary text-xl font-bold md:text-2xl ${className}`}
      >
        {text}
      </span>
      <hr className="border-t-primary w-full" />
    </>
  )
}

export default Headline
