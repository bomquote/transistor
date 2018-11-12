==============
 Contributing
==============

Bug reports, feature requests, and code contributions are encouraged
and welcome!

Bug reports and feature requests
--------------------------------

If you find a bug or have a feature request, please search for
`already reported problems
<https://github.com/bmjjr/transistor/issues>`_ before
submitting a new issue.

Code contributions
------------------

We follow typical `GitHub flow
<https://guides.github.com/introduction/flow/index.html>`_.

1. Fork this repository into your personal space.
2. Start a new topical branch for any contribution.  Name it sensibly,
   say ``improve-fix-search-user-preferences``.
3. Test your branch on a local site.
4. Create logically separate commits for logically separate things.
5. Please add any ``(closes #123)`` or ``(addresses #123)`` directives
   in your commit log message if your pull request closes or addresses
   an open issue.
6. Issue a pull request.  If the branch is not quite ready yet, please
   indicate ``WIP`` (=work in progress) in the pull request title.

Developer Guidelines
--------------------

Here is more detailed checklist of things to do when contributing code.

   * Found a bug in a module and have a fix for it?  Great, please
     jump right in!

   * Have a new feature request or thinking of a new facility that
     would impact several modules?  Submit a issue and discuss the
     change before starting any implementation.

   * Ensure there is a consensus about functionality and design before
     starting any implementation.

   * If you include any code, style, or icons created by others, check
     the original license information to make sure it can be included.

   * Create logically separate commits for logically separate things.

   * Having a basically working version and improving upon its
     performance?  Maintain two separate commits.

   * Committing partially working code and fixing it later?  Squash
     the commits together.

   * Use sensible commit messages and stamp them with QA and ticket directives.

   * Include test cases with the code.

   * Always write unit and/or functional tests alongside coding.  Helps
     making sure the code runs OK on all supported platforms.  Helps
     speeding up the review and integration processes.  Helps
     understanding the code written by others by looking at their unit
     test cases.

   * Include documentation with the code.

   * "It's not finished until it's documented." --This may originally
     have been said by Tom Limoncelli.

   * "Documentation isn't done until someone else understands
     it." --Originally submitted by William S. Annis on 12jan2000.

   * "If the code and the comments disagree, then both are probably
     wrong." --attributed to Norm Schryer

   * "Incorrect documentation is often worse than no
     documentation." --Bertrand Meyer"

   * Check the overall code quality.

   * Does your branch fully implement the functionality it promises to
     implement?  Are all corner cases covered?

   * Does your branch pass Travis or Appveyor builds?

   * Name things properly.  Use ``list_of_scores`` rather than
     ``list2``.  Use ``TransistorBibFooFatalError`` rather than
     ``MyFatalError``.

   * Respect minimal requirements, e.g. write for Python-3.6 for
     production ``maint-x.y`` branches that still require it.

   * Make conditional use of optional dependencies, e.g. test
     ``feedparser`` existence via ``try/except`` importing.  Check
     that the rest of the site still works OK without ``feedparser``.