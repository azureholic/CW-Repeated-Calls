using Microsoft.SemanticKernel;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace cw_repeated_calls_dotnet.Steps
{
    internal class ExitStep : KernelProcessStep
    {
        [KernelFunction]
        public void Exit()
        {
            Console.WriteLine($"{nameof(ExitStep)}:\n\tExiting the process.");
        }
    }
}
