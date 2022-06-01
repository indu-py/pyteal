import pyteal as pt
from pyteal.ast.router import ASTBuilder

import itertools
import pytest

# import random
import typing
import algosdk.abi as sdk_abi


options = pt.CompileOptions(version=5)


@pt.ABIReturnSubroutine
def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:
    return output.set(a.get() + b.get())


@pt.ABIReturnSubroutine
def sub(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:
    return output.set(a.get() - b.get())


@pt.ABIReturnSubroutine
def mul(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:
    return output.set(a.get() * b.get())


@pt.ABIReturnSubroutine
def div(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:
    return output.set(a.get() / b.get())


@pt.ABIReturnSubroutine
def mod(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:
    return output.set(a.get() % b.get())


@pt.ABIReturnSubroutine
def qrem(
    a: pt.abi.Uint64,
    b: pt.abi.Uint64,
    *,
    output: pt.abi.Tuple2[pt.abi.Uint64, pt.abi.Uint64],
) -> pt.Expr:
    return pt.Seq(
        (q := pt.abi.Uint64()).set(a.get() / b.get()),
        (rem := pt.abi.Uint64()).set(a.get() % b.get()),
        output.set(q, rem),
    )


@pt.ABIReturnSubroutine
def reverse(a: pt.abi.String, *, output: pt.abi.String) -> pt.Expr:
    idx = pt.ScratchVar()
    buff = pt.ScratchVar()

    init = idx.store(pt.Int(0))
    cond = idx.load() < a.length()
    _iter = idx.store(idx.load() + pt.Int(1))
    return pt.Seq(
        buff.store(pt.Bytes("")),
        pt.For(init, cond, _iter).Do(
            a[idx.load()].use(lambda v: buff.store(pt.Concat(v.encode(), buff.load())))
        ),
        output.set(buff.load()),
    )


@pt.ABIReturnSubroutine
def concat_strings(
    b: pt.abi.DynamicArray[pt.abi.String], *, output: pt.abi.String
) -> pt.Expr:
    idx = pt.ScratchVar()
    buff = pt.ScratchVar()

    init = idx.store(pt.Int(0))
    cond = idx.load() < b.length()
    _iter = idx.store(idx.load() + pt.Int(1))
    return pt.Seq(
        buff.store(pt.Bytes("")),
        pt.For(init, cond, _iter).Do(
            b[idx.load()].use(lambda s: buff.store(pt.Concat(buff.load(), s.get())))
        ),
        output.set(buff.load()),
    )


@pt.ABIReturnSubroutine
def many_args(
    _a: pt.abi.Uint64,
    _b: pt.abi.Uint64,
    _c: pt.abi.Uint64,
    _d: pt.abi.Uint64,
    _e: pt.abi.Uint64,
    _f: pt.abi.Uint64,
    _g: pt.abi.Uint64,
    _h: pt.abi.Uint64,
    _i: pt.abi.Uint64,
    _j: pt.abi.Uint64,
    _k: pt.abi.Uint64,
    _l: pt.abi.Uint64,
    _m: pt.abi.Uint64,
    _n: pt.abi.Uint64,
    _o: pt.abi.Uint64,
    _p: pt.abi.Uint64,
    _q: pt.abi.Uint64,
    _r: pt.abi.Uint64,
    _s: pt.abi.Uint64,
    _t: pt.abi.Uint64,
    *,
    output: pt.abi.Uint64,
) -> pt.Expr:
    return output.set(_t.get())


@pt.Subroutine(pt.TealType.none)
def safe_clear_state_delete():
    return (
        pt.If(pt.Txn.sender() == pt.Global.creator_address())
        .Then(pt.Approve())
        .Else(pt.Reject())
    )


@pt.ABIReturnSubroutine
def dummy_doing_nothing():
    return pt.Seq(pt.Log(pt.Bytes("a message")))


@pt.Subroutine(pt.TealType.uint64)
def returning_u64():
    return pt.Int(1)


@pt.Subroutine(pt.TealType.none)
def mult_over_u64_and_log(a: pt.Expr, b: pt.Expr):
    return pt.Log(pt.Itob(a * b))


@pt.ABIReturnSubroutine
def eine_constant(*, output: pt.abi.Uint64):
    return output.set(1)


@pt.ABIReturnSubroutine
def take_abi_and_log(tb_logged: pt.abi.String):
    return pt.Log(tb_logged.get())


@pt.ABIReturnSubroutine
def not_registrable(lhs: pt.abi.Uint64, rhs: pt.Expr, *, output: pt.abi.Uint64):
    return output.set(lhs.get() * rhs)


GOOD_SUBROUTINE_CASES: list[pt.ABIReturnSubroutine | pt.SubroutineFnWrapper] = [
    add,
    sub,
    mul,
    div,
    mod,
    qrem,
    reverse,
    concat_strings,
    many_args,
    safe_clear_state_delete,
    dummy_doing_nothing,
    eine_constant,
    take_abi_and_log,
]

ON_COMPLETE_CASES: list[pt.EnumInt] = [
    pt.OnComplete.NoOp,
    pt.OnComplete.OptIn,
    pt.OnComplete.ClearState,
    pt.OnComplete.CloseOut,
    pt.OnComplete.UpdateApplication,
    pt.OnComplete.DeleteApplication,
]


def power_set(no_dup_list: list, length_override: int = None):
    """
    This function serves as a generator for all possible elements in power_set
    over `non_dup_list`, which is a list of non-duplicated elements (matches property of a set).

    The cardinality of a powerset is 2^|non_dup_list|, so we can iterate from 0 to 2^|non_dup_list| - 1
    to index each element in such power_set.
    By binary representation of each index, we can see it as an allowance over each element in `no_dup_list`,
    and generate a unique subset of `non_dup_list`, which yields as an element of power_set of `no_dup_list`.

    Args:
        no_dup_list: a list of elements with no duplication
        length_override: a number indicating the largest size of super_set element,
            must be in range [1, len(no_dup_list)].
    """
    if length_override is None:
        length_override = len(no_dup_list)
    assert 1 <= length_override <= len(no_dup_list)
    masks = [1 << i for i in range(length_override)]
    for i in range(1 << len(no_dup_list)):
        yield [elem for mask, elem in zip(masks, no_dup_list) if i & mask]


def full_perm_gen(non_dup_list: list, perm_length: int):
    """
    This function serves as a generator for all possible vectors of length `perm_length`,
    each of whose entries are one of the elements in `non_dup_list`,
    which is a list of non-duplicated elements.

    Args:
        non_dup_list: must be a list of elements with no duplication
        perm_length: must be a non-negative number indicating resulting length of the vector
    """
    if perm_length < 0:
        raise pt.TealInputError("input permutation length must be non-negative")
    elif len(set(non_dup_list)) != len(non_dup_list):
        raise pt.TealInputError(f"input non_dup_list {non_dup_list} has duplications")
    elif perm_length == 0:
        yield []
        return
    # we can index all possible cases of vectors with an index in range
    # [0, |non_dup_list| ^ perm_length - 1]
    # by converting an index into |non_dup_list|-based number,
    # we can get the vector mapped by the index.
    for index in range(len(non_dup_list) ** perm_length):
        index_list_basis = []
        temp = index
        for _ in range(perm_length):
            index_list_basis.append(non_dup_list[temp % len(non_dup_list)])
            temp //= len(non_dup_list)
        yield index_list_basis


def oncomplete_is_in_oc_list(sth: pt.EnumInt, oc_list: list[pt.EnumInt]):
    return any(map(lambda x: str(x) == str(sth), oc_list))


def assemble_helper(what: pt.Expr) -> pt.TealBlock:
    assembled, _ = what.__teal__(options)
    assembled.addIncoming()
    assembled = pt.TealBlock.NormalizeBlocks(assembled)
    return assembled


def camel_to_snake(name: str) -> str:
    return "".join(["_" + c.lower() if c.isupper() else c for c in name]).lstrip("_")


def test_call_config():
    for cc in pt.CallConfig:
        cond_on_cc: pt.Expr | int = cc.condition_under_config()
        match cond_on_cc:
            case pt.Expr():
                expected_cc = (
                    (pt.Txn.application_id() == pt.Int(0))
                    if cc == pt.CallConfig.CREATE
                    else (pt.Txn.application_id() != pt.Int(0))
                )
                with pt.TealComponent.Context.ignoreExprEquality():
                    assert assemble_helper(cond_on_cc) == assemble_helper(expected_cc)
            case int():
                assert cond_on_cc == int(cc) & 1
            case _:
                raise pt.TealInternalError(f"unexpected cond_on_cc {cond_on_cc}")


def test_method_config():
    never_mc = pt.MethodConfig(no_op=pt.CallConfig.NEVER)
    assert never_mc.is_never()
    assert not never_mc.is_arc4_compliant()
    assert never_mc.approval_cond() == 0
    assert never_mc.clear_state_cond() == 0

    all_mc = pt.MethodConfig.arc4_compliant()
    assert not all_mc.is_never()
    assert all_mc.is_arc4_compliant()
    assert all_mc.approval_cond() == 1
    assert all_mc.clear_state_cond() == 1

    on_complete_pow_set = power_set(ON_COMPLETE_CASES)
    for on_complete_set in on_complete_pow_set:
        oc_names = [camel_to_snake(oc.name) for oc in on_complete_set]
        full_perm_call_configs_for_ocs = full_perm_gen(
            list(pt.CallConfig), len(on_complete_set)
        )
        for call_config in full_perm_call_configs_for_ocs:
            mc = pt.MethodConfig(**dict(zip(oc_names, call_config)))
            approval_list = [
                mc.no_op,
                mc.opt_in,
                mc.close_out,
                mc.update_application,
                mc.delete_application,
            ]
            len(approval_list)

            # method_config: pt.MethodConfig


def test_on_complete_action():
    with pytest.raises(pt.TealInputError) as contradict_err:
        pt.OnCompleteAction(action=pt.Seq(), call_config=pt.CallConfig.NEVER)
    assert "contradicts" in str(contradict_err)
    assert pt.OnCompleteAction.never().is_empty()
    assert pt.OnCompleteAction.call_only(pt.Seq()).call_config == pt.CallConfig.CALL
    assert pt.OnCompleteAction.create_only(pt.Seq()).call_config == pt.CallConfig.CREATE
    assert pt.OnCompleteAction.always(pt.Seq()).call_config == pt.CallConfig.ALL


def test_add_method():
    abi_subroutine_cases = [
        abi_ret
        for abi_ret in GOOD_SUBROUTINE_CASES
        if isinstance(abi_ret, pt.ABIReturnSubroutine)
    ]
    normal_subroutine = [
        subroutine
        for subroutine in GOOD_SUBROUTINE_CASES
        if not isinstance(subroutine, pt.ABIReturnSubroutine)
    ]
    router = pt.Router(
        "routerForMethodTest",
        pt.BareCallActions(clear_state=pt.OnCompleteAction.call_only(pt.Approve())),
    )
    for subroutine in normal_subroutine:
        with pytest.raises(pt.TealInputError) as must_be_abi:
            router.add_method_handler(subroutine)
        assert "for adding method handler, must be ABIReturnSubroutine" in str(
            must_be_abi
        )
    on_complete_pow_set = power_set(ON_COMPLETE_CASES)
    for handler, on_complete_set in itertools.product(
        abi_subroutine_cases, on_complete_pow_set
    ):
        full_perm_call_configs_for_ocs = full_perm_gen(
            list(pt.CallConfig), len(on_complete_set)
        )
        oc_names = [camel_to_snake(oc.name) for oc in on_complete_set]
        for call_config in full_perm_call_configs_for_ocs:
            method_call_configs: pt.MethodConfig = pt.MethodConfig(
                **dict(zip(oc_names, call_config))
            )
            if method_call_configs.is_never():
                with pytest.raises(pt.TealInputError) as call_config_never:
                    router.add_method_handler(handler, None, method_call_configs)
                assert "is never executed" in str(call_config_never)
                continue

            # router.add_method_handler(handler, None, method_call_configs)
            # on_create = method_call_configs.oc_under_call_config(pt.CallConfig.CREATE)
            # on_call = method_call_configs.oc_under_call_config(pt.CallConfig.CALL)


#     for subroutine, on_completes, is_creation in itertools.product(
#         GOOD_SUBROUTINE_CASES, ON_COMPLETE_COMBINED_CASES, [False, True]
#     ):
#         if len(on_completes) == 0:
#             with pytest.raises(pt.TealInputError) as err_no_oc:
#                 pt.Router.parse_conditions(
#                     subroutine if is_abi_subroutine else None,
#                     on_completes,
#                     is_creation,
#                 )
#             assert "on complete input should be non-empty list" in str(err_no_oc)
#             continue
#
#         mutated_on_completes = on_completes + [random.choice(on_completes)]
#         with pytest.raises(pt.TealInputError) as err_dup_oc:
#             pt.Router.parse_conditions(
#                 subroutine if is_abi_subroutine else None,
#                 mutated_on_completes,
#                 is_creation,
#             )
#         assert "has duplicated on_complete(s)" in str(err_dup_oc)
#
#         (
#             approval_condition_list,
#             clear_state_condition_list,
#         ) = pt.Router.parse_conditions(
#             subroutine if is_abi_subroutine else None,
#             on_completes,
#             is_creation,
#         )
#
#         if not oncomplete_is_in_oc_list(pt.OnComplete.ClearState, on_completes):
#             assert len(clear_state_condition_list) == 0
#
#         assembled_ap_condition_list: list[pt.TealBlock] = [
#             assemble_helper(expr) for expr in approval_condition_list
#         ]
#         assembled_csp_condition_list: list[pt.TealBlock] = [
#             assemble_helper(expr) for expr in clear_state_condition_list
#         ]
#         if is_creation:
#             creation_condition: pt.Expr = pt.Txn.application_id() == pt.Int(0)
#             assembled_condition = assemble_helper(creation_condition)
#             with pt.TealComponent.Context.ignoreExprEquality():
#                 assert assembled_condition in assembled_ap_condition_list
#
#         subroutine_arg_cond: pt.Expr
#         if is_abi_subroutine:
#             subroutine_arg_cond = (
#                 pt.MethodSignature(typing.cast(str, method_sig))
#                 == pt.Txn.application_args[0]
#             )
#         else:
#             subroutine_arg_cond = pt.Int(1)
#
#         assembled_condition = assemble_helper(subroutine_arg_cond)
#         with pt.TealComponent.Context.ignoreExprEquality():
#             if not (
#                 len(on_completes) == 1
#                 and oncomplete_is_in_oc_list(pt.OnComplete.ClearState, on_completes)
#             ):
#                 assert assembled_condition in assembled_ap_condition_list
#
#         if oncomplete_is_in_oc_list(pt.OnComplete.ClearState, on_completes):
#             with pt.TealComponent.Context.ignoreExprEquality():
#                 assert assembled_condition in assembled_csp_condition_list
#
#         if len(on_completes) == 1 and oncomplete_is_in_oc_list(
#             pt.OnComplete.ClearState, on_completes
#         ):
#             continue
#
#         on_completes_cond: pt.Expr = pt.Or(
#             *[
#                 pt.Txn.on_completion() == oc
#                 for oc in on_completes
#                 if str(oc) != str(pt.OnComplete.ClearState)
#             ]
#         )
#         on_completes_cond_assembled = assemble_helper(on_completes_cond)
#         with pt.TealComponent.Context.ignoreExprEquality():
#             assert on_completes_cond_assembled in assembled_ap_condition_list


def test_wrap_handler_bare_call():
    BARE_CALL_CASES = [
        dummy_doing_nothing,
        safe_clear_state_delete,
        pt.Approve(),
        pt.Log(pt.Bytes("message")),
    ]
    for bare_call in BARE_CALL_CASES:
        wrapped: pt.Expr = ASTBuilder.wrap_handler(False, bare_call)
        expected: pt.Expr
        match bare_call:
            case pt.Expr():
                if bare_call.has_return():
                    expected = bare_call
                else:
                    expected = pt.Seq(bare_call, pt.Approve())
            case pt.SubroutineFnWrapper() | pt.ABIReturnSubroutine():
                expected = pt.Seq(bare_call(), pt.Approve())
            case _:
                raise pt.TealInputError("how you got here?")
        wrapped_assemble = assemble_helper(wrapped)
        wrapped_helper = assemble_helper(expected)
        with pt.TealComponent.Context.ignoreExprEquality():
            assert wrapped_assemble == wrapped_helper

    ERROR_CASES = [
        (
            pt.Int(1),
            f"bare appcall handler should be TealType.none not {pt.TealType.uint64}.",
        ),
        (
            returning_u64,
            f"subroutine call should be returning TealType.none not {pt.TealType.uint64}.",
        ),
        (
            mult_over_u64_and_log,
            "subroutine call should take 0 arg for bare-app call. this subroutine takes 2.",
        ),
        (
            eine_constant,
            f"abi-returning subroutine call should be returning void not {pt.abi.Uint64TypeSpec()}.",
        ),
        (
            take_abi_and_log,
            "abi-returning subroutine call should take 0 arg for bare-app call. this abi-returning subroutine takes 1.",
        ),
        (
            1,
            "bare appcall can only accept: none type Expr, or Subroutine/ABIReturnSubroutine with none return and no arg",
        ),
    ]
    for error_case, error_msg in ERROR_CASES:
        with pytest.raises(pt.TealInputError) as bug:
            ASTBuilder.wrap_handler(False, error_case)
        assert error_msg in str(bug)


def test_wrap_handler_method_call():
    with pytest.raises(pt.TealInputError) as bug:
        ASTBuilder.wrap_handler(True, not_registrable)
    assert "method call ABIReturnSubroutine is not routable" in str(bug)

    with pytest.raises(pt.TealInputError) as bug:
        ASTBuilder.wrap_handler(True, safe_clear_state_delete)
    assert "method call should be only registering ABIReturnSubroutine" in str(bug)

    ONLY_ABI_SUBROUTINE_CASES = list(
        filter(lambda x: isinstance(x, pt.ABIReturnSubroutine), GOOD_SUBROUTINE_CASES)
    )
    for abi_subroutine in ONLY_ABI_SUBROUTINE_CASES:
        wrapped: pt.Expr = ASTBuilder.wrap_handler(True, abi_subroutine)
        assembled_wrapped: pt.TealBlock = assemble_helper(wrapped)

        args: list[pt.abi.BaseType] = [
            spec.new_instance()
            for spec in typing.cast(
                list[pt.abi.TypeSpec], abi_subroutine.subroutine.expected_arg_types
            )
        ]

        loading: list[pt.Expr]

        if abi_subroutine.subroutine.argument_count() > pt.METHOD_ARG_NUM_CUTOFF:
            sdk_last_arg = pt.abi.TupleTypeSpec(
                *[
                    spec
                    for spec in typing.cast(
                        list[pt.abi.TypeSpec],
                        abi_subroutine.subroutine.expected_arg_types,
                    )[pt.METHOD_ARG_NUM_CUTOFF - 1 :]
                ]
            ).new_instance()
            loading = [
                arg.decode(pt.Txn.application_args[index + 1])
                for index, arg in enumerate(args[: pt.METHOD_ARG_NUM_CUTOFF - 1])
            ]
            loading.append(
                sdk_last_arg.decode(pt.Txn.application_args[pt.METHOD_ARG_NUM_CUTOFF])
            )
            for i in range(pt.METHOD_ARG_NUM_CUTOFF - 1, len(args)):
                loading.append(
                    sdk_last_arg[i - pt.METHOD_ARG_NUM_CUTOFF + 1].store_into(args[i])
                )
        else:
            loading = [
                arg.decode(pt.Txn.application_args[index + 1])
                for index, arg in enumerate(args)
            ]

        evaluate: pt.Expr
        if abi_subroutine.type_of() != "void":
            output_temp = abi_subroutine.output_kwarg_info.abi_type.new_instance()
            evaluate = pt.Seq(
                abi_subroutine(*args).store_into(output_temp),
                pt.abi.MethodReturn(output_temp),
            )
        else:
            evaluate = abi_subroutine(*args)

        actual = assemble_helper(pt.Seq(*loading, evaluate, pt.Approve()))
        with pt.TealComponent.Context.ignoreScratchSlotEquality(), pt.TealComponent.Context.ignoreExprEquality():
            assert actual == assembled_wrapped


def test_contract_json_obj():
    abi_subroutines = list(
        filter(lambda x: isinstance(x, pt.ABIReturnSubroutine), GOOD_SUBROUTINE_CASES)
    )
    contract_name = "contract_name"
    on_complete_actions = pt.BareCallActions(
        clear_state=pt.OnCompleteAction.call_only(safe_clear_state_delete)
    )
    router = pt.Router(contract_name, on_complete_actions)
    method_list: list[sdk_abi.Method] = []
    for subroutine in abi_subroutines:
        router.add_method_handler(subroutine)
        method_list.append(sdk_abi.Method.from_signature(subroutine.method_signature()))
    sdk_contract = sdk_abi.Contract(contract_name, method_list)
    contract = router.contract_construct()
    assert contract == sdk_contract