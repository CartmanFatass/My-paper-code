"""Finite pure checks:16 scalar native references, zero random/native/C queries."""

import numpy as np
import pytest

from envs.pettingzoo.uav_radio import user_sinr_from_path_loss,greedy_connection_assignment,service_metrics
from experiments.candidates.uav_radio_uncertainty.b01 import contract as c,model,protocol as p


def test_batched_radio_matches_original_scalar_greedy_ties_and_empty_eligibility():
    losses=np.full((4,5,50),100.,np.float64)
    losses[0,0]=60.
    losses[1]=80.
    losses[2,0]=np.linspace(60.,100.,50)
    losses[3]=np.arange(250,dtype=np.float64).reshape(5,50)/8.+65.
    for mask in (1,3,7,31):
        native,sinr,grants=model.native_batch(losses,mask)
        for index,loss in enumerate(losses):
            reference=user_sinr_from_path_loss(loss,transmitter_mask=p.mask_array(mask))
            assigned=greedy_connection_assignment(reference)
            values=service_metrics(reference,assigned)
            np.testing.assert_array_equal(sinr[index],reference)
            np.testing.assert_array_equal(grants[index],assigned)
            np.testing.assert_array_equal(native[index],(values["J"],values["served"],values["quality"]))
    # Native stable ties assign lowest user indices when one row saturates.
    np.testing.assert_array_equal(grants[0,0],np.arange(50)<10)


def test_ou_hover_clipped_motion_stationary_variance_and_power_identity():
    positions=np.array([[0.,0.,50.],[1000.,1000.,150.],[100.,200.,100.],[500.,500.,90.],[30.,30.,70.]])
    commands=np.array([[-1,-1,-1],[1,1,1],[1,0,0],[0,0,0],[-1,-1,-1]],np.float64)
    moved,rho=model.move(positions,commands)
    np.testing.assert_array_equal(moved[:2],positions[:2])
    assert rho[0]==rho[1]==rho[3]==1.
    assert rho[2]==np.exp(-30./17.62)
    mean=np.full((5,50),2.)
    variance=np.full((5,50),c.SIGMA_DB**2)
    mu,var=model.moments_step(mean,variance,rho)
    np.testing.assert_allclose(var,variance,rtol=0,atol=1e-14)
    nominal=np.full((5,50),80.)
    effective=model.expected_loss(nominal,mu,var)
    a=np.log(10.)/10.
    np.testing.assert_allclose(10.**((23.-effective)/10.),10.**((23.-nominal)/10.)*np.exp(-a*mu+.5*a*a*var),rtol=1e-14,atol=0)
    residual=np.broadcast_to(mean,(32,5,50)).copy()
    innovation=np.zeros_like(residual)
    updated=model.particles_step(residual,rho,innovation)
    np.testing.assert_array_equal(updated[:,[0,1,3]],residual[:,[0,1,3]])


def test_quantization_map_rounding_codec_delivery_and_saturation():
    values=np.full((5,50),80.)
    values[0,:6]=(39.7,40.25,40.75,167.5,167.75,168.)
    codes,flags=p.encode_losses(values)
    np.testing.assert_array_equal(codes[0,:6],(0,0,2,255,255,255))
    np.testing.assert_array_equal(flags["clipped_low"][0,:6],(True,False,False,False,False,False))
    np.testing.assert_array_equal(flags["clipped_high"][0,:6],(False,False,False,False,True,True))
    own=np.tile((.2,.3,.5),(5,1)).astype(np.float32)
    actual=np.zeros((5,3),np.float32)
    proposed=p.COMMANDS[np.arange(5)]
    packets=p.encode_reports(own,actual,proposed,252,np.arange(5,dtype=np.uint8),codes)
    assert sum(map(len,packets))==375
    decoded=p.decode_reports(packets,252)
    np.testing.assert_array_equal(decoded[0],np.tile((200.,300.,100.),(5,1)))
    np.testing.assert_array_equal(decoded[-1],40.+.5*codes)
    packet=p.encode_command(7,3,12,252)
    assert len(packet)==16 and p.decode_command(packet,252)==(7,3,12)
    assert p.COMMAND.unpack(packet)[5]==255
    sites=np.tile((2.5,3.5),(50,1))
    np.testing.assert_array_equal(p.decode_map(p.encode_map(sites)),np.tile((2.,4.),(50,1)))
    assert abs(sum(c.payload_weight(t) for t in range(256))-249.6)<1e-10
    assert abs(sum(c.payload_weight(t) for t in range(3,256))-246.7)<1e-10
    assert (375+16)*8/2000+.1+c.COMPUTE_SECONDS==3.


@pytest.mark.parametrize("mask",[0,32,True,1.5])
def test_invalid_masks_are_rejected_without_radio_work(mask):
    with pytest.raises(ValueError):
        p.mask_array(mask)
