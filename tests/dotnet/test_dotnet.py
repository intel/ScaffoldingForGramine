import pytest

@pytest.mark.framework
def test_dotnet(cli, docker_run, project_dir, get_image_id):
    assert cli('setup',
        '--framework', 'dotnet',
        '--project_dir', project_dir,
        '--target', 'hello_world',
        '--bootstrap',
    ).exit_code == 0

    result = cli('build', '--project_dir', project_dir, '--print-only-image')
    assert result.exit_code == 0
    image_id = get_image_id(result)

    output = docker_run(image_id)
    assert b'hello, world' in output
