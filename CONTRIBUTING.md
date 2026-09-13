# Contributing to AMD Detection System

Thank you for your interest in contributing to this environmental monitoring research project! Contributions from the global remote sensing community help advance open science and improve environmental protection worldwide.

## How to Contribute

### Reporting Issues
- Use GitHub Issues to report bugs or suggest features
- Provide clear descriptions with reproducible examples
- Include study area coordinates, sensor type, and software versions

### Code Contributions
1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/your-feature-name`)
3. **Make your changes** following the code style guidelines below
4. **Test thoroughly** with multiple study areas
5. **Commit with clear messages** (`git commit -m 'Add validation for X region'`)
6. **Push to your fork** (`git push origin feature/your-feature-name`)
7. **Open a Pull Request** with detailed description of changes

## Code Style Guidelines

### JavaScript (Google Earth Engine)
- Use descriptive variable names (`waterMask` not `wm`)
- Comment complex algorithms with methodology references
- Include units in threshold variable names (`scoreThresholdModerate` not `threshold1`)
- Maintain existing function structure and naming conventions

### Python
- Follow PEP 8 style guidelines
- Use type hints for function parameters
- Include docstrings with parameter descriptions
- Write unit tests for new functions

### Documentation
- Update README.md for new features
- Add entries to CHANGELOG.md following semantic versioning
- Include methodology references in technical documentation
- Provide examples for new functionality

## Areas for Contribution

### High Priority
- **Validation studies**: Test tool in new geographic regions with ground truth data
- **Algorithm optimization**: Improve processing speed for large watersheds
- **Python workflow**: Complete automated batch processing capability
- **Documentation**: Tutorials, video guides, case studies

### Research Opportunities
- **Machine learning integration**: Enhance classification accuracy
- **Temporal analysis**: Trend detection algorithms
- **New sensors**: Integration with additional satellite platforms
- **Hydrological modeling**: Coupling with water quality models

### Community Support
- **Answer questions** in GitHub Discussions
- **Share case studies** from your research applications
- **Translate documentation** to other languages
- **Create educational materials** for workshops/courses

## Testing Requirements

Before submitting code:
1. Test with at least 3 different study areas
2. Verify both Landsat 8/9 and Sentinel-2 sensors work
3. Check water quality classification on known contaminated sites
4. Ensure no errors in Earth Engine Code Editor console
5. Validate spectral index calculations match published methodology

## Commit Message Format

```
<type>: <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code formatting (no logic changes)
- `refactor`: Code restructuring
- `test`: Adding tests
- `perf`: Performance improvements

**Example:**
```
feat: per-scene sigma thresholding for the iron sulfate index

Replaces the absolute > 0.10 cutoff with the paper's per-scene
mean + k*sd method. The absolute cutoff did not transfer: it
over-called 4.1x at the site where it was derived and under-called
5.6x at an independent site.

Worst-case leave-one-site-out Youden J 0.107 -> 0.440 over three
sites against Rockwell's published map (replica fidelity, not
accuracy). Report in validation/REPLICA_AUDIT_2026-07-26.md.

Fixes #42
```

> The previous example in this file read *"Implements adaptive water masking
> using AWEINSH > 0.20 … Validated against Ganau Lake ground truth"*. It was
> replaced 2026-09-13 because it modelled two habits this project has since
> had to retract: putting an **absolute cutoff on a non-normalised index**, and
> calling a **circularly tuned** result "validated". Commit messages here
> should name the measurement, its **n**, and its reference standard.

## Pull Request Guidelines

Your PR should:
- Address a specific issue or feature
- Include clear description of changes and rationale
- Reference any related issues (`Fixes #123`)
- Update relevant documentation
- Pass all existing functionality tests
- Include validation results if modifying detection algorithms

## Code Review Process

1. Maintainer reviews PR within 7 days
2. Feedback provided for any needed changes
3. Once approved, PR merged to main branch
4. Contributor credited in CHANGELOG.md

## Research Collaboration

For larger research collaborations:
- Contact via [www.climtawy.com](https://www.climtawy.com)
- Email: abdulrahman@climtawy.com
- Propose collaboration through GitHub Discussions
- Share preliminary results for methodology validation
- Co-authorship considered for significant contributions

## Questions?

- **General questions**: Open GitHub Discussion
- **Bug reports**: Open GitHub Issue
- **Research collaboration**: Contact through [www.climtawy.com](https://www.climtawy.com)
- **Email**: abdulrahman@climtawy.com
- **Urgent issues**: Email or GitHub Issue

## Code of Conduct

- Be respectful and constructive in all interactions
- Welcome contributors from all backgrounds and experience levels
- Focus on advancing environmental science and open research
- Credit others' work appropriately
- Follow open science principles

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for helping advance environmental monitoring research!** Your contributions support water quality protection and environmental justice worldwide.
