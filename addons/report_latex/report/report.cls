\NeedsTeXFormat{LaTeX2e}[1994/12/01]
\ProvidesClass{report}[2001/05/28 Document Report]

\LoadClass[a4paper]{article}
\RequirePackage{graphicx}
\RequirePackage{fancyhdr}
\RequirePackage[cm]{fullpage}


\renewcommand{\headheight}{0.6in}
\setlength{\headwidth}{\textwidth}
\pagestyle{fancy}
\fancyhf{}


\newcommand{\logo}[1]{
\fancyhead[L]{ #1 }
}

\newcommand{\name}[1]{
\fancyhead[R]{ #1 }
}

